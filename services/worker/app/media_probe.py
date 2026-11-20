"""Deterministic ffprobe/FFmpeg helpers used by Clipro media workers."""
from __future__ import annotations

import hashlib
import json
import subprocess
from fractions import Fraction
from pathlib import Path
from typing import Any


class MediaProbeError(RuntimeError):
    """The uploaded asset is not a valid or supported video."""


def _safe_fraction(value: str | None) -> tuple[int, int]:
    if not value or value in {"0/0", "N/A"}:
        return (0, 1)
    try:
        fraction = Fraction(value)
        if fraction.denominator <= 0 or fraction.numerator < 0:
            return (0, 1)
        return (fraction.numerator, fraction.denominator)
    except (ValueError, ZeroDivisionError):
        return (0, 1)


def probe_media(path: Path, *, timeout_seconds: int = 120) -> dict[str, Any]:
    """Inspect an actual media file. All command arguments are fixed or path values."""
    if not path.is_file() or path.stat().st_size <= 0:
        raise MediaProbeError("The uploaded media file is missing or empty.")

    command = [
        "ffprobe",
        "-v", "error",
        "-show_entries",
        "format=duration,format_name,size:stream=index,codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate,sample_rate,channels",
        "-of", "json",
        str(path),
    ]
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except FileNotFoundError as exc:
        raise MediaProbeError("ffprobe is not installed in the media worker image.") from exc
    except subprocess.TimeoutExpired as exc:
        raise MediaProbeError("Media inspection exceeded its time limit.") from exc
    except subprocess.CalledProcessError as exc:
        # Do not return raw FFmpeg output: it can contain media metadata or paths.
        raise MediaProbeError("ffprobe could not read this video file.") from exc

    try:
        payload = json.loads(completed.stdout)
        streams = payload.get("streams") or []
        video = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
        audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
        format_data = payload.get("format") or {}
        if video is None:
            raise MediaProbeError("The uploaded file does not contain a video stream.")

        duration_seconds = float(format_data.get("duration") or video.get("duration") or 0)
        if duration_seconds <= 0:
            raise MediaProbeError("The video duration could not be determined.")

        fps_num, fps_den = _safe_fraction(
            video.get("avg_frame_rate") or video.get("r_frame_rate")
        )
        width = int(video.get("width") or 0)
        height = int(video.get("height") or 0)
        if width <= 0 or height <= 0:
            raise MediaProbeError("The video dimensions could not be determined.")

        return {
            "duration_ms": round(duration_seconds * 1000),
            "width": width,
            "height": height,
            "frame_rate_num": fps_num,
            "frame_rate_den": fps_den,
            "video_codec": video.get("codec_name"),
            "audio_codec": audio.get("codec_name") if audio else None,
            "has_audio": audio is not None,
            "audio_sample_rate": int(audio["sample_rate"]) if audio and audio.get("sample_rate") else None,
            "audio_channels": int(audio["channels"]) if audio and audio.get("channels") else None,
            "format_name": format_data.get("format_name"),
            "file_size_bytes": path.stat().st_size,
        }
    except (json.JSONDecodeError, TypeError, ValueError, KeyError) as exc:
        if isinstance(exc, MediaProbeError):
            raise
        raise MediaProbeError("ffprobe returned invalid media metadata.") from exc


def sha256_file(path: Path, *, chunk_bytes: int = 8 * 1024 * 1024) -> str:
    """Hash a file incrementally without loading it all into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as file:
        while chunk := file.read(chunk_bytes):
            digest.update(chunk)
    return digest.hexdigest()


def create_thumbnail(
    source: Path,
    destination: Path,
    *,
    duration_ms: int,
    timeout_seconds: int = 90,
) -> None:
    """Extract one representative JPEG frame; no user-supplied filter expressions."""
    timestamp_seconds = min(2.0, max(0.0, duration_ms / 2000))
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "error",
        "-ss", f"{timestamp_seconds:.3f}",
        "-i", str(source),
        "-frames:v", "1",
        "-vf", "scale=640:640:force_original_aspect_ratio=decrease",
        "-q:v", "3",
        "-y",
        str(destination),
    ]
    try:
        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except FileNotFoundError as exc:
        raise MediaProbeError("FFmpeg is not installed in the media worker image.") from exc
    except subprocess.TimeoutExpired as exc:
        raise MediaProbeError("Thumbnail generation exceeded its time limit.") from exc
    except subprocess.CalledProcessError as exc:
        raise MediaProbeError("A thumbnail could not be generated from this video.") from exc

    if not destination.is_file() or destination.stat().st_size == 0:
        raise MediaProbeError("FFmpeg did not produce a thumbnail.")
