"""Platform-aware source rules for live and previously streamed video.

Clipro does not fetch arbitrary third-party livestream URLs. Users capture a
native platform clip or provide authorized media, then upload the actual file
through the browser. Platform instructions are kept separate from editorial
processing so the same renderer can accept all source types.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Platform(str, Enum):
    TWITCH = "twitch"
    KICK = "kick"
    YOUTUBE = "youtube"


class SourceKind(str, Enum):
    LIVE_STREAM = "live_stream"
    PAST_BROADCAST = "past_broadcast"
    UPLOADED_VIDEO = "uploaded_video"


class AcquisitionMode(str, Enum):
    VIEWER_NATIVE_CLIP_MANUAL_DOWNLOAD = "viewer_native_clip_manual_download"
    YOUTUBE_CLIP_REFERENCE = "youtube_clip_reference"
    AUTHORIZED_SOURCE_FILE = "authorized_source_file"
    CREATOR_RELAY = "creator_relay"
    EDITOR_API = "editor_api"


@dataclass(frozen=True, slots=True)
class SourcePolicy:
    platform: Platform
    source_kind: SourceKind
    acquisition_mode: AcquisitionMode
    min_clip_seconds: int | None
    max_clip_seconds: int | None
    requires_file_upload: bool
    can_capture_from_viewer_ui: bool
    notes: tuple[str, ...]


def get_source_policy(platform: Platform, source_kind: SourceKind) -> SourcePolicy:
    """Return the documented manual-source route for a platform/source kind."""
    if platform is Platform.TWITCH:
        return SourcePolicy(
            platform=platform,
            source_kind=source_kind,
            acquisition_mode=AcquisitionMode.VIEWER_NATIVE_CLIP_MANUAL_DOWNLOAD,
            min_clip_seconds=5,
            max_clip_seconds=60,
            requires_file_upload=True,
            can_capture_from_viewer_ui=True,
            notes=(
                "A logged-in viewer can create clips from live streams and past broadcasts when channel settings allow it.",
                "Download the clip you created from Twitch Clips Manager, then upload the MP4 to Clipro.",
                "The editor-only Get Clips Download API is not used in viewer mode.",
            ),
        )

    if platform is Platform.KICK:
        return SourcePolicy(
            platform=platform,
            source_kind=source_kind,
            acquisition_mode=AcquisitionMode.VIEWER_NATIVE_CLIP_MANUAL_DOWNLOAD,
            min_clip_seconds=10,
            max_clip_seconds=180,
            requires_file_upload=True,
            can_capture_from_viewer_ui=True,
            notes=(
                "A logged-in viewer can create clips from live streams and VODs when clipping is enabled.",
                "Download the clip you created from its Kick clip page, then upload the MP4 to Clipro.",
                "A viewer cannot download another channel's full VOD; use the native clip workflow or creator-supplied media.",
            ),
        )

    return SourcePolicy(
        platform=platform,
        source_kind=source_kind,
        acquisition_mode=AcquisitionMode.AUTHORIZED_SOURCE_FILE,
        min_clip_seconds=5,
        max_clip_seconds=60,
        requires_file_upload=True,
        can_capture_from_viewer_ui=False,
        notes=(
            "YouTube Clips are shareable references to a source video, not a direct MP4 export for Clipro's renderer.",
            "Live Clips have DVR and broadcast-length restrictions and may not become playable until the stream ends and the archive is available.",
            "Upload an authorized source file or excerpt from the creator/campaign for custom editing.",
        ),
    )


@dataclass(frozen=True, slots=True)
class SourceSubmission:
    platform: Platform
    source_kind: SourceKind
    acquisition_mode: AcquisitionMode
    file_uploaded: bool
    source_permission_confirmed: bool
    source_url: str | None = None


@dataclass(frozen=True, slots=True)
class SourceValidation:
    accepted: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


def validate_source_submission(submission: SourceSubmission) -> SourceValidation:
    """Validate source handoff before it enters AI analysis/rendering.

    No public stream URL alone is treated as a downloadable video asset.
    """
    errors: list[str] = []
    warnings: list[str] = []
    policy = get_source_policy(submission.platform, submission.source_kind)

    if not submission.source_permission_confirmed:
        errors.append("confirm that the campaign/creator authorizes editing and publishing this source")

    if submission.acquisition_mode is AcquisitionMode.EDITOR_API:
        errors.append(
            "Editor API acquisition is not enabled in viewer mode; use your own native clip download"
        )

    if submission.platform is Platform.YOUTUBE:
        if submission.acquisition_mode is AcquisitionMode.YOUTUBE_CLIP_REFERENCE:
            if not submission.file_uploaded:
                errors.append(
                    "a YouTube Clip URL is a reference only; upload an authorized source video file for editing"
                )
        elif submission.acquisition_mode is not AcquisitionMode.AUTHORIZED_SOURCE_FILE:
            errors.append("YouTube custom editing requires an authorized source file")
        if not submission.file_uploaded:
            errors.append("upload an authorized video file before processing")
    else:
        if submission.acquisition_mode is not AcquisitionMode.VIEWER_NATIVE_CLIP_MANUAL_DOWNLOAD:
            errors.append("use a viewer-created native clip downloaded manually from the platform")
        if not submission.file_uploaded:
            errors.append("download the clip you created and upload its video file to Clipro")

    if submission.source_kind is SourceKind.UPLOADED_VIDEO:
        warnings.append(
            "Uploaded full VODs may be large; trim to an authorized excerpt or use the browser's source-range selector"
        )

    return SourceValidation(not errors, tuple(errors), tuple(warnings))
