"""Source upload preflight contracts.

This module validates submitted metadata before an upload session is created.
It does not download a source URL, accept arbitrary URLs as media, or claim
that the bytes have been probed. Actual media inspection happens after storage.
"""
from __future__ import annotations

from enum import StrEnum
from urllib.parse import urlparse

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator


MAX_UPLOAD_BYTES = 20 * 1024 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".m4v",
    ".webm",
    ".mkv",
}

EXTENSION_MIME_TYPES = {
    ".mp4": {"video/mp4", "application/octet-stream"},
    ".mov": {"video/quicktime", "application/octet-stream"},
    ".m4v": {"video/x-m4v", "video/mp4", "application/octet-stream"},
    ".webm": {"video/webm", "application/octet-stream"},
    ".mkv": {"video/x-matroska", "application/octet-stream"},
}


class Platform(StrEnum):
    TWITCH = "twitch"
    KICK = "kick"
    YOUTUBE = "youtube"
    UPLOAD = "upload"


class SourceKind(StrEnum):
    LIVE_STREAM = "live_stream"
    PAST_BROADCAST = "past_broadcast"
    UPLOADED_VIDEO = "uploaded_video"


class AcquisitionMode(StrEnum):
    VIEWER_NATIVE_CLIP_MANUAL_DOWNLOAD = "viewer_native_clip_manual_download"
    AUTHORIZED_SOURCE_FILE = "authorized_source_file"


class RightsStatus(StrEnum):
    CREATOR_AUTHORIZED = "creator_authorized"
    USER_OWNED = "user_owned"
    LICENSED = "licensed"
    PUBLIC_DOMAIN = "public_domain"
    PENDING_REVIEW = "pending_review"


class UploadPreflightRequest(BaseModel):
    """Metadata needed to decide whether a source may enter the upload flow."""

    model_config = ConfigDict(extra="forbid")

    original_filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=3, max_length=120)
    file_size_bytes: int = Field(gt=0, le=MAX_UPLOAD_BYTES)
    platform: Platform
    source_kind: SourceKind
    acquisition_mode: AcquisitionMode
    streamer_id: str | None = Field(default=None, min_length=1, max_length=128)
    campaign_id: str | None = Field(default=None, min_length=1, max_length=128)
    source_url: AnyHttpUrl | None = None
    permission_confirmed: bool = False
    rights_status: RightsStatus = RightsStatus.PENDING_REVIEW
    rights_notes: str | None = Field(default=None, max_length=2000)

    @field_validator("original_filename")
    @classmethod
    def normalize_filename(cls, value: str) -> str:
        # Treat both slash styles as separators; never persist a submitted path.
        filename = value.replace("\\", "/").rsplit("/", 1)[-1].strip()
        if not filename or filename in {".", ".."}:
            raise ValueError("a valid video filename is required")
        return filename

    @field_validator("content_type")
    @classmethod
    def normalize_content_type(cls, value: str) -> str:
        return value.split(";", 1)[0].strip().lower()

    @field_validator("streamer_id", "campaign_id")
    @classmethod
    def normalize_optional_ids(cls, value: str | None) -> str | None:
        return value.strip() if value else None


class UploadPreflightResponse(BaseModel):
    accepted: bool
    errors: list[str]
    warnings: list[str]
    max_file_size_bytes: int = MAX_UPLOAD_BYTES


def validate_upload_preflight(
    submission: UploadPreflightRequest,
) -> UploadPreflightResponse:
    """Validate acquisition and declared file metadata without touching media."""

    errors: list[str] = []
    warnings: list[str] = []

    filename_lower = submission.original_filename.lower()
    extension = "." + filename_lower.rsplit(".", 1)[-1] if "." in filename_lower else ""

    if extension not in ALLOWED_EXTENSIONS:
        errors.append(
            "Unsupported video format. Upload MP4, MOV, M4V, WebM or MKV."
        )
    elif submission.content_type not in EXTENSION_MIME_TYPES[extension]:
        errors.append(
            "The declared MIME type does not match the filename extension."
        )

    if not submission.permission_confirmed:
        errors.append(
            "Confirm that you have permission to edit and publish this source."
        )

    if submission.rights_status is RightsStatus.PENDING_REVIEW:
        errors.append(
            "Confirm the source rights status before sending it for processing."
        )

    if submission.campaign_id and not submission.streamer_id:
        errors.append("A campaign upload must be associated with a streamer.")

    if (
        submission.acquisition_mode
        is AcquisitionMode.VIEWER_NATIVE_CLIP_MANUAL_DOWNLOAD
    ):
        if submission.platform not in {Platform.TWITCH, Platform.KICK}:
            errors.append(
                "Viewer-created native clip uploads are currently supported only for Twitch and Kick."
            )
        if submission.source_kind is SourceKind.UPLOADED_VIDEO:
            errors.append(
                "Use authorized_source_file for an ordinary uploaded video."
            )

    if submission.platform is Platform.UPLOAD:
        if submission.source_kind is not SourceKind.UPLOADED_VIDEO:
            errors.append(
                "The generic upload source must use source_kind=uploaded_video."
            )
        if (
            submission.acquisition_mode
            is not AcquisitionMode.AUTHORIZED_SOURCE_FILE
        ):
            errors.append(
                "Generic uploaded videos must use authorized_source_file."
            )

    if (
        submission.platform is Platform.YOUTUBE
        and submission.acquisition_mode
        is AcquisitionMode.VIEWER_NATIVE_CLIP_MANUAL_DOWNLOAD
    ):
        errors.append(
            "A YouTube Clip URL is a reference, not a downloadable editing file. Upload an authorized source file."
        )

    if (
        submission.acquisition_mode is AcquisitionMode.AUTHORIZED_SOURCE_FILE
        and submission.source_kind is SourceKind.UPLOADED_VIDEO
        and submission.platform in {Platform.TWITCH, Platform.KICK}
    ):
        warnings.append(
            "For a long source video, Clipro should probe it first and analyze it in bounded time ranges."
        )

    if submission.source_url is not None:
        host = (urlparse(str(submission.source_url)).hostname or "").lower()
        if not host:
            errors.append("The source URL is not valid.")
        elif submission.platform is Platform.TWITCH and not (
            host == "twitch.tv" or host.endswith(".twitch.tv")
        ):
            warnings.append(
                "The source URL host does not look like Twitch; it will be stored as a reference only."
            )
        elif submission.platform is Platform.KICK and not (
            host == "kick.com" or host.endswith(".kick.com")
        ):
            warnings.append(
                "The source URL host does not look like Kick; it will be stored as a reference only."
            )
        elif submission.platform is Platform.YOUTUBE and not (
            host in {"youtube.com", "youtu.be"}
            or host.endswith(".youtube.com")
        ):
            warnings.append(
                "The source URL host does not look like YouTube; it will be stored as a reference only."
            )

    if submission.source_kind is SourceKind.UPLOADED_VIDEO:
        warnings.append(
            "The uploaded file must be creator-authorized, user-owned, licensed or public-domain; Clipro will probe the actual media after upload."
        )

    return UploadPreflightResponse(
        accepted=not errors,
        errors=errors,
        warnings=warnings,
    )
