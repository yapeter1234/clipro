"""Official Twitch Helix client for authorized live/VOD clipping.

For the Diego pilot, the clipper must be explicitly added as a channel Editor
by the broadcaster, then authenticate their own Twitch account with
editor:manage:clips. This does not use undocumented playback URL extraction.

Temporary Twitch CDN download URLs are sensitive and must never be logged or
persisted as durable public URLs.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Iterable

import httpx


HELIX_BASE_URL = "https://api.twitch.tv/helix"


class TwitchAPIError(RuntimeError):
    """A sanitized Twitch Helix API error."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(slots=True)
class TwitchHelixClient:
    """Async Twitch Helix client using one user's OAuth access token."""

    client_id: str
    user_access_token: str
    http_client: httpx.AsyncClient | None = None
    base_url: str = HELIX_BASE_URL
    _owns_client: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.client_id.strip():
            raise ValueError("client_id is required")
        if not self.user_access_token.strip():
            raise ValueError("user_access_token is required")
        if self.http_client is None:
            self.http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(20.0, connect=10.0),
                follow_redirects=False,
            )
            self._owns_client = True

    async def aclose(self) -> None:
        if self._owns_client and self.http_client is not None:
            await self.http_client.aclose()

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.user_access_token}",
            "Client-Id": self.client_id,
            "Accept": "application/json",
        }

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | list[tuple[str, Any]] | None = None,
    ) -> dict[str, Any]:
        assert self.http_client is not None
        # Build an absolute URL so the /helix prefix is preserved even when
        # an injected AsyncClient has its own base_url.
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        response = await self.http_client.request(
            method,
            url,
            params=params,
            headers=self._headers,
        )
        if response.is_error:
            try:
                payload = response.json()
                message = str(payload.get("message") or "Twitch API request failed")
            except (ValueError, AttributeError):
                message = "Twitch API request failed"
            raise TwitchAPIError(response.status_code, message)
        try:
            payload = response.json()
        except ValueError as exc:
            raise TwitchAPIError(
                response.status_code,
                "Twitch API returned a non-JSON response",
            ) from exc
        if not isinstance(payload, dict):
            raise TwitchAPIError(
                response.status_code,
                "Twitch API returned an unexpected response shape",
            )
        return payload

    async def get_user(self, login: str) -> dict[str, Any] | None:
        if not login.strip():
            raise ValueError("login is required")
        result = await self._request(
            "GET", "/users", params={"login": login.strip().lstrip("@")}
        )
        rows = result.get("data") or []
        return rows[0] if rows else None

    async def get_stream(self, broadcaster_id: str) -> dict[str, Any] | None:
        result = await self._request(
            "GET", "/streams", params={"user_id": broadcaster_id}
        )
        rows = result.get("data") or []
        return rows[0] if rows else None

    async def list_vods(
        self,
        broadcaster_id: str,
        *,
        first: int = 20,
        after: str | None = None,
        video_type: str = "archive",
    ) -> dict[str, Any]:
        if not 1 <= first <= 100:
            raise ValueError("first must be between 1 and 100")
        params: dict[str, Any] = {
            "user_id": broadcaster_id,
            "type": video_type,
            "first": first,
        }
        if after:
            params["after"] = after
        return await self._request("GET", "/videos", params=params)

    async def list_clips(
        self,
        broadcaster_id: str,
        *,
        started_at: str | None = None,
        ended_at: str | None = None,
        first: int = 20,
        after: str | None = None,
    ) -> dict[str, Any]:
        if not 1 <= first <= 100:
            raise ValueError("first must be between 1 and 100")
        params: dict[str, Any] = {
            "broadcaster_id": broadcaster_id,
            "first": first,
        }
        if started_at:
            params["started_at"] = started_at
        if ended_at:
            if not started_at:
                raise ValueError("ended_at requires started_at")
            params["ended_at"] = ended_at
        if after:
            params["after"] = after
        return await self._request("GET", "/clips", params=params)

    async def get_clips_by_ids(self, clip_ids: Iterable[str]) -> dict[str, Any]:
        ids = [value for value in clip_ids if value]
        if not ids or len(ids) > 100:
            raise ValueError("provide between 1 and 100 clip IDs")
        params = [("id", value) for value in ids]
        return await self._request("GET", "/clips", params=params)

    async def create_live_clip(
        self,
        broadcaster_id: str,
        *,
        title: str | None = None,
        duration: float = 30.0,
        has_delay: bool = False,
    ) -> dict[str, Any]:
        """Create a native clip from a currently live broadcast (clips:edit)."""
        if not 5 <= duration <= 60:
            raise ValueError("duration must be between 5 and 60 seconds")
        params: dict[str, Any] = {
            "broadcaster_id": broadcaster_id,
            "duration": duration,
            "has_delay": str(has_delay).lower(),
        }
        if title:
            params["title"] = title[:140]
        return await self._request("POST", "/clips", params=params)

    async def create_vod_clip(
        self,
        *,
        editor_id: str,
        broadcaster_id: str,
        vod_id: str,
        vod_offset: int,
        title: str,
        duration: float = 30.0,
    ) -> dict[str, Any]:
        """Create a clip from a VOD, including a VOD being recorded live.

        Requires editor:manage:clips or channel:manage:clips. The clip starts
        at (vod_offset - duration) and ends at vod_offset.
        """
        if not 5 <= duration <= 60:
            raise ValueError("duration must be between 5 and 60 seconds")
        if vod_offset < duration:
            raise ValueError("vod_offset must be >= duration")
        if not title.strip():
            raise ValueError("title is required")
        params = {
            "editor_id": editor_id,
            "broadcaster_id": broadcaster_id,
            "vod_id": vod_id,
            "vod_offset": vod_offset,
            "duration": duration,
            "title": title[:140],
        }
        return await self._request("POST", "/videos/clips", params=params)

    async def wait_for_clip(
        self,
        clip_id: str,
        *,
        timeout_seconds: float = 60.0,
        poll_interval_seconds: float = 2.0,
    ) -> dict[str, Any] | None:
        """Poll Get Clips until Twitch returns the newly created clip."""
        if timeout_seconds <= 0 or poll_interval_seconds <= 0:
            raise ValueError("timeout and poll interval must be positive")
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            result = await self.get_clips_by_ids([clip_id])
            rows = result.get("data") or []
            if rows:
                return rows[0]
            await asyncio.sleep(poll_interval_seconds)
        return None

    async def get_clip_downloads(
        self,
        *,
        editor_id: str,
        broadcaster_id: str,
        clip_ids: Iterable[str],
    ) -> dict[str, Any]:
        """Get temporary download URLs for authorized channel clips.

        Requires editor:manage:clips or channel:manage:clips. The editor_id
        must match the user ID represented by the OAuth token. Fetch returned
        URLs promptly, and never log/store them as public permanent URLs.
        """
        ids = [clip_id for clip_id in clip_ids if clip_id]
        if not ids or len(ids) > 10:
            raise ValueError("provide between 1 and 10 clip IDs")
        params: list[tuple[str, Any]] = [
            ("editor_id", editor_id),
            ("broadcaster_id", broadcaster_id),
        ]
        params.extend(("clip_id", clip_id) for clip_id in ids)
        return await self._request("GET", "/clips/downloads", params=params)
