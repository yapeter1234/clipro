"""Async Postgres pool and workspace membership checks."""
from __future__ import annotations

import asyncio
from typing import Any
from uuid import UUID

import asyncpg

from .settings import get_settings

_pool: asyncpg.Pool | None = None
_pool_lock = asyncio.Lock()
WRITE_ROLES = {"owner", "admin", "editor"}


def _database_dsn() -> str:
    value = get_settings().database_url
    if not value:
        raise RuntimeError("DATABASE_URL is not configured")
    return value.replace("postgresql+asyncpg://", "postgresql://", 1)


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is not None:
        return _pool

    async with _pool_lock:
        if _pool is not None:
            return _pool
        settings = get_settings()
        try:
            _pool = await asyncpg.create_pool(
                dsn=_database_dsn(),
                ssl="require" if settings.database_ssl else None,
                min_size=1,
                max_size=8,
                command_timeout=30,
                statement_cache_size=0,
            )
        except (OSError, asyncpg.PostgresError, RuntimeError) as exc:
            raise RuntimeError("Could not connect to Clipro Postgres.") from exc
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def require_workspace_membership(
    workspace_id: UUID, user_id: UUID, *, write: bool = False
) -> dict[str, Any]:
    from fastapi import HTTPException, status

    pool = await get_pool()
    async with pool.acquire() as connection:
        row = await connection.fetchrow(
            """SELECT workspace_id, user_id, role
               FROM public.workspace_memberships
               WHERE workspace_id = $1 AND user_id = $2""",
            workspace_id,
            user_id,
        )

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this workspace.",
        )

    membership = dict(row)
    if write and membership["role"] not in WRITE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your workspace role does not permit this action.",
        )
    return membership


async def fetch_upload_session(storage_upload_id: str, storage_key: str) -> dict[str, Any]:
    from fastapi import HTTPException

    pool = await get_pool()
    async with pool.acquire() as connection:
        row = await connection.fetchrow(
            """SELECT us.upload_session_id, us.asset_id, us.workspace_id,
                      us.storage_upload_id, us.storage_key, us.status,
                      us.expires_at, ma.uploaded_by, ma.file_size_bytes
               FROM public.upload_sessions AS us
               JOIN public.media_assets AS ma ON ma.asset_id = us.asset_id
               WHERE us.storage_upload_id = $1 AND us.storage_key = $2""",
            storage_upload_id,
            storage_key,
        )

    if row is None:
        raise HTTPException(status_code=404, detail="Upload session was not found.")
    return dict(row)
