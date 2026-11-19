"""Orchestrate authorized Twitch VOD clip creation for one candidate moment.

This module requests an unlisted/native Twitch clip as a source artifact; it
does not publish anything to external social networks. A human still approves
the final edited MP4 in Clipro.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services.api.app.providers.twitch import TwitchHelixClient
from services.worker.app.twitch_vod_window import VodClipWindow, plan_vod_clip_window


class ClipNotReady(RuntimeError):
    """The active Twitch VOD has not yet reached the desired clip end offset."""


class TwitchClipCreationError(RuntimeError):
    """Twitch did not return a usable created clip."""


@dataclass(frozen=True, slots=True)
class AcquiredTwitchClip:
    clip_id: str
    vod_id: str
    window: VodClipWindow
    download_url: str


async def create_and_get_twitch_vod_clip(
    client: TwitchHelixClient,
    *,
    editor_id: str,
    broadcaster_id: str,
    vod_id: str,
    stream_started_at,
    event_at,
    now,
    title: str,
    pre_roll_seconds: float = 30.0,
    post_roll_seconds: float = 15.0,
    estimated_vod_lag_seconds: float = 20.0,
) -> AcquiredTwitchClip:
    """Create a VOD clip once its requested source window should be available.

    The caller should schedule a retry at window.ready_at when ClipNotReady is
    raised. Temporary CDN URLs must be fetched promptly and never logged.
    """
    window = plan_vod_clip_window(
        stream_started_at=stream_started_at,
        event_at=event_at,
        now=now,
        pre_roll_seconds=pre_roll_seconds,
        post_roll_seconds=post_roll_seconds,
        estimated_vod_lag_seconds=estimated_vod_lag_seconds,
    )
    if window.wait_seconds > 0:
        raise ClipNotReady(
            f"active VOD should reach the candidate window in {window.wait_seconds:.1f}s"
        )

    response = await client.create_vod_clip(
        editor_id=editor_id,
        broadcaster_id=broadcaster_id,
        vod_id=vod_id,
        vod_offset=window.vod_offset_seconds,
        title=title,
        duration=window.duration_seconds,
    )
    rows = response.get("data") or []
    if not rows or not rows[0].get("id"):
        raise TwitchClipCreationError("Twitch did not return a clip ID")
    clip_id = str(rows[0]["id"])

    clip = await client.wait_for_clip(clip_id, timeout_seconds=60, poll_interval_seconds=2)
    if not clip:
        raise TwitchClipCreationError("Twitch did not make the created clip available")

    downloads = await client.get_clip_downloads(
        editor_id=editor_id,
        broadcaster_id=broadcaster_id,
        clip_ids=[clip_id],
    )
    download_rows = downloads.get("data") or []
    if not download_rows:
        raise TwitchClipCreationError("Twitch did not return an authorized download URL")

    download_url = (
        download_rows[0].get("portrait_download_url")
        or download_rows[0].get("landscape_download_url")
    )
    if not download_url:
        raise TwitchClipCreationError("Twitch returned no available clip media URL")

    return AcquiredTwitchClip(
        clip_id=clip_id,
        vod_id=vod_id,
        window=window,
        download_url=str(download_url),
    )
