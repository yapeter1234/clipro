"""Supabase access-token verification using the project's asymmetric JWKS."""
from __future__ import annotations

from functools import lru_cache
from typing import Any
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError, PyJWKClient, PyJWKClientError
from pydantic import BaseModel

from .settings import get_settings

bearer_scheme = HTTPBearer(auto_error=False)


class CurrentUser(BaseModel):
    user_id: UUID
    email: str | None = None


@lru_cache(maxsize=4)
def _jwks_client(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(jwks_url, cache_jwk_set=True, cache_keys=True, lifespan=600, timeout=5)


def _decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    if not settings.supabase_url:
        raise RuntimeError("SUPABASE_URL is not configured")

    issuer = f"{settings.supabase_url.rstrip('/')}/auth/v1"
    jwks_url = f"{issuer}/.well-known/jwks.json"
    signing_key = _jwks_client(jwks_url).get_signing_key_from_jwt(token)

    # The API intentionally requires Supabase ES256 or RS256 signing keys.
    # Legacy HS256 JWT-secret verification is not enabled by this adapter.
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["ES256", "RS256"],
        audience=settings.supabase_jwt_audience,
        issuer=issuer,
        options={"require": ["exp", "iat", "sub"]},
        leeway=30,
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid Supabase access token is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    from starlette.concurrency import run_in_threadpool

    try:
        claims = await run_in_threadpool(_decode_access_token, credentials.credentials)
        user_id = UUID(str(claims["sub"]))
    except (InvalidTokenError, PyJWKClientError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The access token is invalid or expired.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from None

    email = claims.get("email")
    return CurrentUser(user_id=user_id, email=str(email) if email else None)
