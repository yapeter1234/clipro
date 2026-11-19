"""Campaign gates: generic franchise checks plus campaign-specific constraints.

Stream metadata is only a preliminary gate. The final media inspection must
verify what is visibly happening in the video and whether the creator appears.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


DIEGO_TWITCH_LOGIN = "diegoloveless"

_GTA_CATEGORY_RE = re.compile(
    r"^(?:grand theft auto(?:\s+(?:iii|iv|v|vi|online|san andreas|vice city))?|gta\s*(?:[1-6]|iii|iv|v|vi|online))$",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class EligibilityResult:
    eligible: bool
    reasons: tuple[str, ...]


def is_grand_theft_auto_category(game_name: str | None) -> bool:
    """Return True only for a recognized Grand Theft Auto game/category name."""
    if not game_name:
        return False
    normalized = " ".join(game_name.strip().lower().split())
    return bool(_GTA_CATEGORY_RE.fullmatch(normalized))


def evaluate_diego_gta_stream(
    stream: dict[str, Any] | None,
    *,
    expected_login: str = DIEGO_TWITCH_LOGIN,
) -> EligibilityResult:
    """Require Diego's Twitch channel to be live in a Grand Theft Auto category.

    This is a metadata check only. A separate visual gate must verify that the
    submitted media actually shows Diego playing the relevant GTA title.
    """
    reasons: list[str] = []
    if not stream:
        return EligibilityResult(False, ("stream is offline or unavailable",))

    actual_login = str(stream.get("user_login") or "").strip().lower()
    if actual_login != expected_login.strip().lower():
        reasons.append("stream is not from the required DiegoLoveless channel")

    if str(stream.get("type") or "").lower() != "live":
        reasons.append("stream is not marked live")

    game_name = str(stream.get("game_name") or "")
    if not is_grand_theft_auto_category(game_name):
        reasons.append("stream category is not a recognized Grand Theft Auto title")

    return EligibilityResult(not reasons, tuple(reasons))


def evaluate_diego_gta6_stream(
    stream: dict[str, Any] | None,
    *,
    expected_login: str = DIEGO_TWITCH_LOGIN,
) -> EligibilityResult:
    """Backward-compatible alias; campaign rules now use the GTA franchise."""
    return evaluate_diego_gta_stream(stream, expected_login=expected_login)
