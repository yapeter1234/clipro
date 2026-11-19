from datetime import datetime, timedelta, timezone

import pytest

from services.worker.app.twitch_vod_window import plan_vod_clip_window


def test_vod_window_uses_offset_as_clip_end_and_waits_for_vod_edge():
    start = datetime(2026, 11, 19, 12, 0, tzinfo=timezone.utc)
    event = start + timedelta(seconds=120)
    now = start + timedelta(seconds=135)

    plan = plan_vod_clip_window(
        stream_started_at=start,
        event_at=event,
        now=now,
        pre_roll_seconds=30,
        post_roll_seconds=15,
        estimated_vod_lag_seconds=20,
    )

    assert plan.source_start_offset_seconds == 90
    assert plan.source_end_offset_seconds == 135
    assert plan.duration_seconds == 45
    assert plan.vod_offset_seconds == 135
    # Available VOD edge is 115 sec (135 elapsed - 20 sec lag),
    # so the source window needs another 20 sec.
    assert plan.wait_seconds == 20


def test_vod_window_ready_when_stream_vod_has_caught_up():
    start = datetime(2026, 11, 19, 12, 0, tzinfo=timezone.utc)
    event = start + timedelta(seconds=120)
    now = start + timedelta(seconds=160)
    plan = plan_vod_clip_window(
        stream_started_at=start,
        event_at=event,
        now=now,
        pre_roll_seconds=30,
        post_roll_seconds=15,
        estimated_vod_lag_seconds=20,
    )
    assert plan.wait_seconds == 0


def test_vod_window_handles_early_stream_by_clamping_start_to_zero():
    start = datetime(2026, 11, 19, 12, 0, tzinfo=timezone.utc)
    event = start + timedelta(seconds=10)
    now = start + timedelta(seconds=90)
    plan = plan_vod_clip_window(
        stream_started_at=start,
        event_at=event,
        now=now,
        pre_roll_seconds=30,
        post_roll_seconds=15,
        estimated_vod_lag_seconds=20,
    )
    assert plan.source_start_offset_seconds == 0
    assert plan.source_end_offset_seconds == 25
    assert plan.duration_seconds == 25
    assert plan.wait_seconds == 0


def test_vod_window_requires_timezone_aware_timestamps():
    start = datetime(2026, 11, 19, 12, 0)
    with pytest.raises(ValueError, match="timezone-aware"):
        plan_vod_clip_window(
            stream_started_at=start,
            event_at=start,
            now=start,
        )


def test_vod_window_rejects_longer_than_60_seconds():
    start = datetime(2026, 11, 19, 12, 0, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="between 5 and 60"):
        plan_vod_clip_window(
            stream_started_at=start,
            event_at=start + timedelta(seconds=120),
            now=start + timedelta(seconds=200),
            pre_roll_seconds=50,
            post_roll_seconds=20,
        )
