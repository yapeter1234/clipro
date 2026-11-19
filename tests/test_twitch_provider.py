import asyncio

import httpx
import pytest

from services.api.app.providers.twitch import TwitchAPIError, TwitchHelixClient


def make_client(handler):
    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(
        transport=transport,
        base_url="https://api.twitch.test/helix",
    )
    return TwitchHelixClient(
        client_id="test-client",
        user_access_token="test-token",
        http_client=http_client,
        base_url="https://api.twitch.test/helix",
    ), http_client


def test_create_vod_clip_uses_editor_endpoint_and_parameters():
    seen = {}

    def handler(request: httpx.Request):
        seen["url"] = str(request.url)
        seen["authorization"] = request.headers.get("Authorization")
        return httpx.Response(
            202,
            json={"data": [{"id": "clip-123", "edit_url": "https://clips.twitch.tv/edit"}]},
        )

    async def run():
        client, http_client = make_client(handler)
        try:
            result = await client.create_vod_clip(
                editor_id="editor-1",
                broadcaster_id="broadcaster-1",
                vod_id="vod-1",
                vod_offset=120,
                duration=30,
                title="Funny GTA moment",
            )
            assert result["data"][0]["id"] == "clip-123"
        finally:
            await http_client.aclose()

    asyncio.run(run())
    assert seen["url"].startswith("https://api.twitch.test/helix/videos/clips?")
    assert "editor_id=editor-1" in seen["url"]
    assert "vod_offset=120" in seen["url"]
    assert seen["authorization"] == "Bearer test-token"


def test_clip_download_repeats_clip_id_query_parameter():
    seen = {}

    def handler(request: httpx.Request):
        seen["query"] = request.url.query.decode()
        return httpx.Response(
            200,
            json={"data": [{"clip_id": "clip-1", "portrait_download_url": "https://temporary.test/file"}]},
        )

    async def run():
        client, http_client = make_client(handler)
        try:
            result = await client.get_clip_downloads(
                editor_id="editor-1",
                broadcaster_id="broadcaster-1",
                clip_ids=["clip-1", "clip-2"],
            )
            assert result["data"][0]["clip_id"] == "clip-1"
        finally:
            await http_client.aclose()

    asyncio.run(run())
    assert "clip_id=clip-1" in seen["query"]
    assert "clip_id=clip-2" in seen["query"]


def test_vod_clip_validates_duration_and_offset():
    def handler(request: httpx.Request):
        return httpx.Response(500)

    async def run():
        client, http_client = make_client(handler)
        try:
            with pytest.raises(ValueError):
                await client.create_vod_clip(
                    editor_id="editor-1",
                    broadcaster_id="broadcaster-1",
                    vod_id="vod-1",
                    vod_offset=10,
                    duration=30,
                    title="Invalid offset",
                )
            with pytest.raises(ValueError):
                await client.create_vod_clip(
                    editor_id="editor-1",
                    broadcaster_id="broadcaster-1",
                    vod_id="vod-1",
                    vod_offset=60,
                    duration=61,
                    title="Too long",
                )
        finally:
            await http_client.aclose()

    asyncio.run(run())


def test_api_error_does_not_expose_access_token():
    def handler(request: httpx.Request):
        return httpx.Response(403, json={"message": "Clipping is disabled"})

    async def run():
        client, http_client = make_client(handler)
        try:
            with pytest.raises(TwitchAPIError) as exc:
                await client.get_stream("broadcaster-1")
            assert exc.value.status_code == 403
            assert "test-token" not in str(exc.value)
        finally:
            await http_client.aclose()

    asyncio.run(run())


def test_client_can_create_and_close_its_own_http_client():
    async def run():
        client = TwitchHelixClient(
            client_id="test-client",
            user_access_token="test-token",
        )
        assert client.http_client is not None
        assert client._owns_client is True
        await client.aclose()

    asyncio.run(run())
