"""Translate live chat candidate timestamps into Twitch VOD clip windows."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True, slots=True)
class VodClipWindow:
    source_start_offset_seconds: float
    source_end_offset_seconds: float
    duration_seconds: float
    vod_offset_seconds: int
    ready_at: datetime
    wait_seconds: float


def plan_vod_clip_window(
    *,
    stream_started_at: datetime,
    event_at: datetime,
    now: datetime,
    pre_roll_seconds: float = 30.0,
    post_roll_seconds: float = 15.0,
    estimated_vod_lag_seconds: float = 20.0,
) -> VodClipWindow:
    """Plan a clip around an event and determine when the active VOD has caught up.

    Twitch's Create Clip From VOD uses vod_offset as the clip END position:
    clip_start = vod_offset - duration. This planner keeps the source window
    between 5 and 60 seconds and waits until the VOD edge should contain it.
    All datetimes must be timezone-aware.
    """
    for name, value in (
        ("stream_started_at", stream_started_at),
        ("event_at", event_at),
        ("now", now),
    ):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{name} must be timezone-aware")
    if pre_roll_seconds < 0 or post_roll_seconds < 0:
        raise ValueError("pre-roll and post-roll cannot be negative")
    duration = pre_roll_seconds + post_roll_seconds
    if not 5 <= duration <= 60:
        raise ValueError("clip duration must be between 5 and 60 seconds")
    if estimated_vod_lag_seconds < 0:
        raise ValueError("estimated VOD lag cannot be negative")

    started = stream_started_at.astimezone(timezone.utc)
    event = event_at.astimezone(timezone.utc)
    current = now.astimezone(timezone.utc)
    event_offset = (event - started).total_seconds()
    if event_offset < 0:
        raise ValueError("event timestamp predates the stream")
    current_elapsed = (current - started).total_seconds()
    if current_elapsed < 0:
        raise ValueError("current time predates the stream")

    clip_start = max(0.0, event_offset - pre_roll_seconds)
    clip_end = event_offset + post_roll_seconds
    actual_duration = clip_end - clip_start
    if not 5 <= actual_duration <= 60:
        raise ValueError("planned clip duration is outside Twitch's 5–60 second range")

    # Twitch's VOD offset is the end point of the clip.
    vod_offset = int(round(clip_end))
    available_edge = max(0.0, current_elapsed - estimated_vod_lag_seconds)
    wait_seconds = max(0.0, clip_end - available_edge)
    ready_at = current + timedelta(seconds=wait_seconds)

    return VodClipWindow(
        source_start_offset_seconds=round(clip_start, 3),
        source_end_offset_seconds=round(clip_end, 3),
        duration_seconds=round(actual_duration, 3),
        vod_offset_seconds=vod_offset,
        ready_at=ready_at,
        wait_seconds=round(wait_seconds, 3),
    )
