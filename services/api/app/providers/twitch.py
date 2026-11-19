"""Minimal official Twitch Helix client for authorized VOD clipping.

This module never extracts undocumented player URLs. For VOD clipping and
media download, authenticate as a Twitch channel Editor (or the broadcaster)
and request the editor:manage:clips scope.
"""
from __future__ import annotations

from dataclasses import dataclass
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
    """Async Twitch Helix client using one user's OAuth access token.

    Pass a shared httpx.AsyncClient in tests or when reusing a configured
    connection pool. The caller owns and closes an injected client.
    """

    client_id: str
    user_access_token: str
    http_client: httpx.AsyncClient | None = None
    base_url: str = HELIX_BASE_URL

    def __post_init__(self) -> None:
        if not self.client_id.strip():
            raise ValueError("client_id is required")
        if not self.user_access_token.strip():
            raise ValueError("user_access_token is required")
        if self.http_client is None:
            self.http_client = httpx.AsyncClient(
                base_url=self.base_url.rstrip("/"),
                timeout=httpx.Timeout(20.0, connect=10.0),
                follow_redirects=False,
            )
            self._owns_client = True
        else:
            self._owns_client = False

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
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        assert self.http_client is not None
        response = await self.http_client.request(
            method,
            path,
            params=params,
            json=json_body,
            headers=self._headers,
        )
        if response.is_error:
            # Do not include request headers, token values, or signed media URLs
            # in logs or exception text.
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
        """Resolve a Twitch login to a broadcaster record."""
        if not login.strip():
            raise ValueError("login is required")
        result = await self._request(
            "GET",
            "/users",
            params={"login": login.strip().lstrip("@")},
        )
        rows = result.get("data") or []
        return rows[0] if rows else None

    async def get_stream(self, broadcaster_id: str) -> dict[str, Any] | None:
        """Return the active stream record, or None when offline."""
        result = await self._request(
            "GET",
            "/streams",
            params={"user_id": broadcaster_id},
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
        """List channel VODs. Continue pagination using the returned cursor."""
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
        """List a broadcaster's clips, optionally within a time window."""
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

    async def create_live_clip(
        self,
        broadcaster_id: str,
        *,
        title: str | None = None,
        duration: float = 30.0,
        has_delay: bool = False,
    ) -> dict[str, Any]:
        """Request a native clip from a currently live broadcast.

        Requires a user token with clips:edit. The channel must have clipping
        enabled and must not restrict clipping beyond the user's status.
        """
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
        """Create a clip from an archive VOD or the VOD of an active stream.

        Requires editor:manage:clips (or channel:manage:clips for the owner).
        The offset is the clip end position in the VOD, not its start position.
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

    async def get_clip_downloads(
        self,
        *,
        editor_id: str,
        broadcaster_id: str,
        clip_ids: Iterable[str],
    ) -> dict[str, Any]:
        """Get short-lived landscape/portrait download URLs for authorized clips.

        Requires editor:manage:clips or channel:manage:clips. The editor_id
        must match the user represented by the OAuth token. Treat returned
        URLs as secrets: fetch promptly and never log or persist them publicly.
        """
        ids = [clip_id for clip_id in clip_ids if clip_id]
        if not ids or len(ids) > 10:
            raise ValueError("provide between 1 and 10 clip IDs")
        params: list[tuple[str, Any]] = [
            ("editor_id", editor_id),
            ("broadcaster_id", broadcaster_id),
        ]
        params.extend(("clip_id", clip_id) for clip_id in ids)
        return await self._request(
            "GET",
            "/clips/downloads",
            params=params,
        )
