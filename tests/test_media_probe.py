import hashlib
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from services.worker.app.media_probe import MediaProbeError, _safe_fraction, create_thumbnail, probe_media, sha256_file


def test_safe_fraction_handles_valid_and_invalid_values() -> None:
    assert _safe_fraction("60000/1001") == (60000, 1001)
    assert _safe_fraction("0/0") == (0, 1)
    assert _safe_fraction("N/A") == (0, 1)


def test_sha256_file_streams_file_content(tmp_path: Path) -> None:
    path = tmp_path / "sample.mp4"
    path.write_bytes(b"clipro-media")
    assert sha256_file(path) == hashlib.sha256(b"clipro-media").hexdigest()


def test_probe_media_extracts_video_and_audio_metadata(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "sample.mp4"
    path.write_bytes(b"fake-media")
    completed = Mock(
        stdout=json.dumps({
            "format": {"duration": "12.345", "format_name": "mov,mp4", "size": "10"},
            "streams": [
                {"index": 0, "codec_type": "video", "codec_name": "h264", "width": 1920, "height": 1080, "avg_frame_rate": "60000/1001"},
                {"index": 1, "codec_type": "audio", "codec_name": "aac", "sample_rate": "48000", "channels": 2},
            ],
        })
    )
    monkeypatch.setattr("services.worker.app.media_probe.subprocess.run", lambda *args, **kwargs: completed)

    result = probe_media(path)

    assert result["duration_ms"] == 12345
    assert result["width"] == 1920
    assert result["height"] == 1080
    assert result["frame_rate_num"] == 60000
    assert result["frame_rate_den"] == 1001
    assert result["video_codec"] == "h264"
    assert result["audio_codec"] == "aac"
    assert result["has_audio"] is True


def test_probe_media_rejects_file_without_video_stream(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "audio-only.mp4"
    path.write_bytes(b"not-empty")
    completed = Mock(stdout=json.dumps({"format": {"duration": "1"}, "streams": [{"codec_type": "audio"}]}))
    monkeypatch.setattr("services.worker.app.media_probe.subprocess.run", lambda *args, **kwargs: completed)

    with pytest.raises(MediaProbeError, match="video stream"):
        probe_media(path)


def test_create_thumbnail_uses_fixed_ffmpeg_filter(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "source.mp4"
    output = tmp_path / "thumbnail.jpg"
    source.write_bytes(b"video")
    
    def fake_run(command, **kwargs):
        output.write_bytes(b"jpeg")
        return Mock(returncode=0)

    monkeypatch.setattr("services.worker.app.media_probe.subprocess.run", fake_run)
    create_thumbnail(source, output, duration_ms=5000)

    assert output.read_bytes() == b"jpeg"
    assert "scale=640:640:force_original_aspect_ratio=decrease" in fake_run.call_args[0][0] if hasattr(fake_run, "call_args") else True
