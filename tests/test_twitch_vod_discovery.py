import asyncio

from services.worker.app.twitch_vod_discovery import find_vod_for_active_stream


class FakeTwitchClient:
    def __init__(self, page):
        self.page = page
        self.calls = []

    async def list_vods(self, broadcaster_id, *, first=20, after=None, video_type="archive"):
        self.calls.append((broadcaster_id, first, video_type))
        return self.page


def test_active_vod_must_match_stream_and_broadcaster():
    client = FakeTwitchClient({
        "data": [
            {
                "id": "old-vod",
                "stream_id": "old-stream",
                "user_id": "creator-1",
                "type": "archive",
                "title": "Previous GTA stream",
            },
            {
                "id": "current-vod",
                "stream_id": "current-stream",
                "user_id": "creator-1",
                "type": "archive",
                "title": "Live GTA VI broadcast",
                "duration": "1h2m",
            },
            {
                "id": "wrong-owner",
                "stream_id": "current-stream",
                "user_id": "other-user",
                "type": "archive",
            },
        ]
    })

    result = asyncio.run(
        find_vod_for_active_stream(
            client,
            broadcaster_id="creator-1",
            stream_id="current-stream",
        )
    )
    assert result is not None
    assert result.vod_id == "current-vod"
    assert result.stream_id == "current-stream"
    assert client.calls == [("creator-1", 100, "archive")]


def test_no_vod_is_returned_if_active_stream_id_is_not_found():
    client = FakeTwitchClient({
        "data": [
            {
                "id": "previous-vod",
                "stream_id": "previous-stream",
                "user_id": "creator-1",
                "type": "archive",
            }
        ]
    })
    result = asyncio.run(
        find_vod_for_active_stream(
            client,
            broadcaster_id="creator-1",
            stream_id="active-stream",
        )
    )
    assert result is None


def test_requires_broadcaster_and_stream_ids():
    client = FakeTwitchClient({"data": []})
    try:
        asyncio.run(
            find_vod_for_active_stream(
                client,
                broadcaster_id="",
                stream_id="stream-1",
            )
        )
        assert False, "expected ValueError"
    except ValueError:
        pass
