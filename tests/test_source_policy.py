from services.worker.app.source_policy import (
    AcquisitionMode,
    Platform,
    SourceKind,
    SourceSubmission,
    get_source_policy,
    validate_source_submission,
)


def test_twitch_supports_viewer_clips_from_live_and_past_broadcasts():
    for kind in (SourceKind.LIVE_STREAM, SourceKind.PAST_BROADCAST):
        policy = get_source_policy(Platform.TWITCH, kind)
        assert policy.can_capture_from_viewer_ui is True
        assert policy.requires_file_upload is True
        assert policy.min_clip_seconds == 5
        assert policy.max_clip_seconds == 60


def test_kick_supports_viewer_clips_from_live_and_past_broadcasts():
    for kind in (SourceKind.LIVE_STREAM, SourceKind.PAST_BROADCAST):
        policy = get_source_policy(Platform.KICK, kind)
        assert policy.can_capture_from_viewer_ui is True
        assert policy.min_clip_seconds == 10
        assert policy.max_clip_seconds == 180


def test_youtube_requires_authorized_source_file_for_custom_editing():
    policy = get_source_policy(Platform.YOUTUBE, SourceKind.PAST_BROADCAST)
    assert policy.requires_file_upload is True
    assert policy.can_capture_from_viewer_ui is False
    assert policy.acquisition_mode is AcquisitionMode.AUTHORIZED_SOURCE_FILE


def test_twitch_manual_clip_file_is_accepted():
    result = validate_source_submission(
        SourceSubmission(
            platform=Platform.TWITCH,
            source_kind=SourceKind.PAST_BROADCAST,
            acquisition_mode=AcquisitionMode.VIEWER_NATIVE_CLIP_MANUAL_DOWNLOAD,
            file_uploaded=True,
            source_permission_confirmed=True,
            source_url="https://www.twitch.tv/videos/example",
        )
    )
    assert result.accepted is True
    assert not result.errors


def test_public_url_alone_is_not_a_video_file():
    result = validate_source_submission(
        SourceSubmission(
            platform=Platform.TWITCH,
            source_kind=SourceKind.LIVE_STREAM,
            acquisition_mode=AcquisitionMode.VIEWER_NATIVE_CLIP_MANUAL_DOWNLOAD,
            file_uploaded=False,
            source_permission_confirmed=True,
            source_url="https://www.twitch.tv/someone",
        )
    )
    assert result.accepted is False
    assert any("upload its video file" in item for item in result.errors)


def test_editor_only_route_is_rejected_in_manual_viewer_mode():
    result = validate_source_submission(
        SourceSubmission(
            platform=Platform.TWITCH,
            source_kind=SourceKind.PAST_BROADCAST,
            acquisition_mode=AcquisitionMode.EDITOR_API,
            file_uploaded=True,
            source_permission_confirmed=True,
        )
    )
    assert result.accepted is False
    assert any("Editor API" in item for item in result.errors)


def test_youtube_clip_link_without_file_is_rejected():
    result = validate_source_submission(
        SourceSubmission(
            platform=Platform.YOUTUBE,
            source_kind=SourceKind.LIVE_STREAM,
            acquisition_mode=AcquisitionMode.YOUTUBE_CLIP_REFERENCE,
            file_uploaded=False,
            source_permission_confirmed=True,
            source_url="https://youtube.com/clip/example",
        )
    )
    assert result.accepted is False
    assert any("reference only" in item for item in result.errors)
