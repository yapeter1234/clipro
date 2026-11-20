"""Short-lived, signed Clipro operator API-token verification."""
from __future__ import annotations

from typing import Any
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from pydantic import BaseModel

from .settings import get_settings

OPERATOR_USER_ID = UUID("00000000-0000-4000-8000-000000000001")
bearer_scheme = HTTPBearer(auto_error=False)


class CurrentUser(BaseModel):
    """The single Clipro operator identity used by transitional DB ownership checks."""

    user_id: UUID


def _decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    secret = settings.clipro_api_token_secret
    if not secret or len(secret) < 32:
        raise RuntimeError("CLIPRO_API_TOKEN_SECRET is not configured correctly.")

    claims = jwt.decode(
        token,
        secret,
        algorithms=["HS256"],
        audience=settings.clipro_api_token_audience,
        issuer=settings.clipro_api_token_issuer,
        options={"require": ["exp", "iat", "sub", "iss", "aud"]},
        leeway=15,
    )
    if claims.get("sub") != str(OPERATOR_USER_ID):
        raise InvalidTokenError("Unexpected Clipro operator identity.")
    return claims


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid Clipro operator API token is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        _decode_access_token(credentials.credentials)
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The operator API token is invalid or expired.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Clipro API authentication is not configured.",
        ) from None

    return CurrentUser(user_id=OPERATOR_USER_ID)
