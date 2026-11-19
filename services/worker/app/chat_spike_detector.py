"""Low-cost chat-spike candidate detector for a single live Twitch channel."""
from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable


HYPE_RE = re.compile(
    r"(?i)(\bno way\b|\bwtf\b|\bholy\b|\bclip that\b|\blmao\b|\bwtf\b|\blets go\b|\binsane\b|\bwhat\b|\b💀|😂|🤣|🔥|😱)"
)
NOISE_RE = re.compile(
    r"(?i)(giveaway|\braid(ing|ed)?\b|\bbrb\b|ad break|sponsored|promo code|discord\.gg|https?://)"
)
WORD_RE = re.compile(r"[\w']{2,}|[💀😂🤣🔥😱]")


@dataclass(frozen=True, slots=True)
class ChatSample:
    received_at: datetime
    user_id: str | None
    username: str | None
    text: str
    message_id: str | None = None


@dataclass(frozen=True, slots=True)
class ChatSpike:
    detected_at: datetime
    window_start: datetime
    window_end: datetime
    message_count: int
    unique_users: int
    hype_messages: int
    score: float
    sample_messages: tuple[str, ...]


class ChatSpikeDetector:
    """Detect anomalous chat bursts without treating chat as ground-truth video.

    This is a first-pass candidate generator. It must be combined with the
    actual clip's transcript/video review before a candidate is rendered.
    """

    def __init__(
        self,
        *,
        window_seconds: int = 12,
        baseline_seconds: int = 180,
        min_messages: int = 10,
        min_unique_users: int = 5,
        burst_ratio: float = 2.5,
        cooldown_seconds: int = 45,
        max_history_seconds: int = 240,
    ) -> None:
        if window_seconds < 3 or baseline_seconds <= window_seconds:
            raise ValueError("invalid detector window/baseline configuration")
        self.window_seconds = window_seconds
        self.baseline_seconds = baseline_seconds
        self.min_messages = min_messages
        self.min_unique_users = min_unique_users
        self.burst_ratio = burst_ratio
        self.cooldown_seconds = cooldown_seconds
        self.history: deque[ChatSample] = deque()
        self.seen_message_ids: set[str] = set()
        self.last_spike_at: datetime | None = None
        self.max_history_seconds = max_history_seconds

    def _prune(self, now: datetime) -> None:
        cutoff = now.timestamp() - self.max_history_seconds
        while self.history and self.history[0].received_at.timestamp() < cutoff:
            self.history.popleft()

    def add(self, message: ChatSample) -> ChatSpike | None:
        now = message.received_at
        self._prune(now)
        if not message.text.strip() or NOISE_RE.search(message.text):
            return None
        if message.message_id and message.message_id in self.seen_message_ids:
            return None
        if message.message_id:
            self.seen_message_ids.add(message.message_id)
            if len(self.seen_message_ids) > 20_000:
                # Bounded memory for a long-running stream. Old IDs are only
                # retained for duplicate protection during the active window.
                self.seen_message_ids.clear()
                self.seen_message_ids.add(message.message_id)

        self.history.append(message)
        current_end = now.timestamp()
        window_start_ts = current_end - self.window_seconds
        baseline_start_ts = current_end - self.baseline_seconds

        current = [
            item for item in self.history
            if window_start_ts <= item.received_at.timestamp() <= current_end
        ]
        baseline = [
            item for item in self.history
            if baseline_start_ts <= item.received_at.timestamp() < window_start_ts
        ]

        if len(current) < self.min_messages:
            return None
        unique_users = {
            item.user_id or item.username
            for item in current
            if item.user_id or item.username
        }
        if len(unique_users) < self.min_unique_users:
            return None

        current_rate = len(current) / self.window_seconds
        baseline_rate = (len(baseline) / max(1, self.baseline_seconds - self.window_seconds))
        # Require an absolute burst as well as an anomaly. The 0.15 floor
        # avoids an infinite ratio when the recent baseline is quiet.
        if current_rate < max(0.15, baseline_rate * self.burst_ratio):
            return None

        if self.last_spike_at and (
            now - self.last_spike_at
        ).total_seconds() < self.cooldown_seconds:
            return None

        hype = sum(1 for item in current if HYPE_RE.search(item.text))
        score = min(
            10.0,
            4.0
            + min(3.0, current_rate / max(0.15, baseline_rate + 0.05))
            + min(2.0, hype / max(1, len(current)) * 4.0)
            + min(1.0, len(unique_users) / 20.0),
        )
        sample = tuple(
            item.text[:180]
            for item in current[-8:]
        )
        self.last_spike_at = now
        return ChatSpike(
            detected_at=now.astimezone(timezone.utc),
            window_start=datetime.fromtimestamp(window_start_ts, timezone.utc),
            window_end=now.astimezone(timezone.utc),
            message_count=len(current),
            unique_users=len(unique_users),
            hype_messages=hype,
            score=round(score, 2),
            sample_messages=sample,
        )

    def extend(self, messages: Iterable[ChatSample]) -> list[ChatSpike]:
        spikes: list[ChatSpike] = []
        for message in messages:
            candidate = self.add(message)
            if candidate is not None:
                spikes.append(candidate)
        return spikes
