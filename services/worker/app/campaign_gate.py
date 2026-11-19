"""Campaign eligibility gates for the DiegoLoveless GTA 6 pilot.

Stream metadata is a first-pass gate. A later video inspection stage must still
verify that frames show GTA 6 gameplay and that the creator is visible.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


DIEGO_TWITCH_LOGIN = "diegoloveless"
GTA_VI_GAME_NAME_ALIASES = {
    "grand theft auto vi",
    "gta vi",
    "gta 6",
}


@dataclass(frozen=True, slots=True)
class EligibilityResult:
    eligible: bool
    reasons: tuple[str, ...]


def evaluate_diego_gta6_stream(
    stream: dict[str, Any] | None,
    *,
    expected_login: str = DIEGO_TWITCH_LOGIN,
) -> EligibilityResult:
    """Require the correct live broadcaster and GTA VI category."""
    reasons: list[str] = []
    if not stream:
        return EligibilityResult(False, ("stream is offline or unavailable",))

    actual_login = str(stream.get("user_login") or "").strip().lower()
    if actual_login != expected_login.strip().lower():
        reasons.append("stream is not from the required DiegoLoveless channel")

    if str(stream.get("type") or "").lower() != "live":
        reasons.append("stream is not marked live")

    game_name = " ".join(str(stream.get("game_name") or "").strip().lower().split())
    if game_name not in GTA_VI_GAME_NAME_ALIASES:
        reasons.append("stream category is not Grand Theft Auto VI")

    return EligibilityResult(not reasons, tuple(reasons))
