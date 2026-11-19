from datetime import datetime, timedelta, timezone

from services.api.app.providers.twitch_irc import parse_privmsg
from services.worker.app.chat_spike_detector import ChatSample, ChatSpikeDetector


def test_parse_privmsg_extracts_tags_and_text():
    line = (
        "@badge-info=;badges=;display-name=TestUser;id=msg-123;user-id=42 "
        ":testuser!testuser@testuser.tmi.twitch.tv PRIVMSG #diegoloveless :NO WAY 😂"
    )
    event = parse_privmsg(line, "diegoloveless")
    assert event is not None
    assert event.channel == "diegoloveless"
    assert event.message_id == "msg-123"
    assert event.user_id == "42"
    assert event.display_name == "TestUser"
    assert event.text == "NO WAY 😂"


def test_parse_privmsg_ignores_other_channels_and_non_messages():
    assert parse_privmsg(":tmi.twitch.tv PING :tmi.twitch.tv", "diegoloveless") is None
    line = "@display-name=Someone :someone!x PRIVMSG #other :hello"
    assert parse_privmsg(line, "diegoloveless") is None


def test_chat_spike_requires_burst_and_unique_users():
    detector = ChatSpikeDetector(
        window_seconds=10,
        baseline_seconds=60,
        min_messages=8,
        min_unique_users=5,
        burst_ratio=2.0,
        cooldown_seconds=30,
    )
    start = datetime(2026, 11, 19, 12, 0, tzinfo=timezone.utc)

    # Establish a low baseline.
    for index in range(6):
        event = ChatSample(
            received_at=start + timedelta(seconds=index * 5),
            user_id=f"baseline-{index}",
            username=f"baseline{index}",
            text="hello",
        )
        detector.add(event)

    spike = None
    for index in range(10):
        event = ChatSample(
            received_at=start + timedelta(seconds=55 + index * 0.5),
            user_id=f"viewer-{index}",
            username=f"viewer{index}",
            text="NO WAY 😂" if index % 2 == 0 else "LOL",
        )
        candidate = detector.add(event)
        if candidate is not None:
            spike = candidate

    assert spike is not None
    assert spike.message_count >= 8
    assert spike.unique_users >= 5
    assert spike.hype_messages > 0
    assert 0 < spike.score <= 10


def test_spam_and_noise_are_not_scored():
    detector = ChatSpikeDetector(min_messages=4, min_unique_users=3)
    start = datetime(2026, 11, 19, 12, 0, tzinfo=timezone.utc)
    for index in range(10):
        candidate = detector.add(
            ChatSample(
                received_at=start + timedelta(seconds=index),
                user_id=f"u{index}",
                username=f"user{index}",
                text="https://example.com giveaway",
            )
        )
        assert candidate is None
