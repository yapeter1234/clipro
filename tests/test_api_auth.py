from types import SimpleNamespace
from uuid import UUID

import jwt
import pytest
from jwt import InvalidTokenError

from services.api.app import auth


SECRET = "a" * 64
OPERATOR_ID = "00000000-0000-4000-8000-000000000001"


@pytest.fixture
def configured_settings(monkeypatch):
    monkeypatch.setattr(
        auth,
        "get_settings",
        lambda: SimpleNamespace(
            clipro_api_token_secret=SECRET,
            clipro_api_token_issuer="clipro-web",
            clipro_api_token_audience="clipro-api",
        ),
    )


def issue_token(**overrides):
    import time

    now = int(time.time())
    claims = {
        "sub": OPERATOR_ID,
        "iss": "clipro-web",
        "aud": "clipro-api",
        "iat": now,
        "exp": now + 300,
    }
    claims.update(overrides)
    return jwt.encode(claims, SECRET, algorithm="HS256")


def test_accepts_valid_operator_api_token(configured_settings):
    claims = auth._decode_access_token(issue_token())
    assert claims["sub"] == OPERATOR_ID
    assert auth.OPERATOR_USER_ID == UUID(OPERATOR_ID)


@pytest.mark.parametrize(
    "overrides",
    [
        {"aud": "wrong-audience"},
        {"iss": "wrong-issuer"},
        {"sub": "00000000-0000-4000-8000-000000000099"},
        {"exp": 1},
    ],
)
def test_rejects_invalid_operator_api_tokens(configured_settings, overrides):
    with pytest.raises(InvalidTokenError):
        auth._decode_access_token(issue_token(**overrides))


def test_rejects_token_signed_with_another_secret(configured_settings):
    token = jwt.encode(
        {
            "sub": OPERATOR_ID,
            "iss": "clipro-web",
            "aud": "clipro-api",
            "iat": 1_900_000_000,
            "exp": 1_900_000_300,
        },
        "b" * 64,
        algorithm="HS256",
    )
    with pytest.raises(InvalidTokenError):
        auth._decode_access_token(token)
