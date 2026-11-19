"""Read-only Twitch IRC client.

Uses Twitch's documented WebSocket IRC endpoint. Only chat:read is requested;
this client never sends chat messages. Keep the OAuth token in server-side
secrets and never include it in logs or exceptions.
"""
from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import AsyncIterator

from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed


class TwitchChatError(RuntimeError):
    """Sanitized Twitch IRC connection error."""


@dataclass(frozen=True, slots=True)
class TwitchChatMessage:
    channel: str
    message_id: str | None
    user_id: str | None
    username: str | None
    display_name: str | None
    text: str
    received_at: datetime


_TAG_ESCAPE = {
    r"\s": " ",
    r"\:": ";",
    r"\\": "\\",
    r"\r": "\r",
    r"\n": "\n",
}


def _unescape_tag(value: str) -> str:
    return re.sub(
        r"\\([snr:\\])",
        lambda match: _TAG_ESCAPE.get(match.group(0), match.group(1)),
        value,
    )


def parse_privmsg(line: str, channel: str) -> TwitchChatMessage | None:
    """Parse one IRC PRIVMSG line. Ignore all non-chat messages."""
    if not line.startswith("@") or " PRIVMSG " not in line:
        return None

    tag_text, _, remainder = line[1:].partition(" ")
    prefix, sep, trailing = remainder.partition(" :")
    if not sep or not prefix.startswith(":"):
        return None

    parts = prefix.split(" ")
    if len(parts) < 2 or parts[0] == "":
        return None

    user_prefix = parts[0].lstrip(":")
    username = user_prefix.split("!", 1)[0] or None
    target = parts[1].lstrip("#").lower()
    if target != channel.lower().lstrip("#"):
        return None

    tags: dict[str, str] = {}
    for item in tag_text.split(";"):
        key, equals, value = item.partition("=")
        if key:
            tags[key] = _unescape_tag(value) if equals else ""

    text = trailing.strip()
    if not text:
        return None

    return TwitchChatMessage(
        channel=target,
        message_id=tags.get("id") or None,
        user_id=tags.get("user-id") or None,
        username=username,
        display_name=tags.get("display-name") or username,
        text=text,
        received_at=datetime.now(timezone.utc),
    )


class TwitchIRCReader:
    """Read one Twitch channel's public chat over the official IRC WebSocket."""

    endpoint = "wss://irc-ws.chat.twitch.tv:443"

    def __init__(
        self,
        *,
        channel: str,
        username: str,
        user_access_token: str,
        reconnect_delay_seconds: float = 3.0,
    ) -> None:
        self.channel = channel.strip().lower().lstrip("#")
        self.username = username.strip().lower().lstrip("@")
        self.user_access_token = user_access_token.strip()
        self.reconnect_delay_seconds = max(1.0, reconnect_delay_seconds)
        if not self.channel or not self.username or not self.user_access_token:
            raise ValueError("channel, username and user access token are required")

    async def messages(self) -> AsyncIterator[TwitchChatMessage]:
        """Yield chat messages, reconnecting after a dropped WebSocket."""
        while True:
            try:
                async with connect(
                    self.endpoint,
                    open_timeout=15,
                    close_timeout=5,
                    ping_interval=20,
                    ping_timeout=20,
                    max_size=64 * 1024,
                ) as websocket:
                    await websocket.send(f"PASS oauth:{self.user_access_token}")
                    await websocket.send(f"NICK {self.username}")
                    await websocket.send(
                        "CAP REQ :twitch.tv/tags twitch.tv/commands"
                    )
                    await websocket.send(f"JOIN #{self.channel}")

                    authenticated = False
                    async for raw in websocket:
                        line = str(raw)
                        if line.startswith("PING"):
                            payload = line.partition(" ")[2] or ":tmi.twitch.tv"
                            await websocket.send(f"PONG {payload}")
                            continue
                        if " 001 " in line:
                            authenticated = True
                            continue
                        if "Login authentication failed" in line or "Improperly formatted auth" in line:
                            raise TwitchChatError(
                                "Twitch IRC rejected the chat-read credentials"
                            )
                        if " 421 " in line or " NOTICE " in line:
                            # Keep connection notices out of user-facing errors.
                            continue
                        if not authenticated:
                            continue
                        event = parse_privmsg(line, self.channel)
                        if event is not None:
                            yield event
            except TwitchChatError:
                raise
            except (OSError, TimeoutError, ConnectionClosed):
                await asyncio.sleep(self.reconnect_delay_seconds)
            except asyncio.CancelledError:
                raise
