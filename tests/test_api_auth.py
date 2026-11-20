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


@pytest.fixture
def api_client(configured_settings):
    from fastapi.testclient import TestClient

    from services.api.app.auth import get_current_user
    from services.api.app.main import app

    # The upload-policy module installs an override for its own tests at
    # import time. Remove it here so these requests exercise real auth.
    previous = app.dependency_overrides.pop(get_current_user, None)
    try:
        with TestClient(app) as client:
            yield client
    finally:
        if previous is not None:
            app.dependency_overrides[get_current_user] = previous


def valid_preflight_payload():
    return {
        "original_filename": "authorized-clip.mp4",
        "content_type": "video/mp4",
        "file_size_bytes": 25_000_000,
        "platform": "twitch",
        "source_kind": "live_stream",
        "acquisition_mode": "viewer_native_clip_manual_download",
        "streamer_id": "diegoloveless",
        "campaign_id": "diego-gta",
        "source_url": "https://www.twitch.tv/diegoloveless/clip/example",
        "permission_confirmed": True,
        "rights_status": "creator_authorized",
    }


def test_api_rejects_preflight_without_bearer_token(api_client):
    response = api_client.post(
        "/api/v1/uploads/preflight",
        json=valid_preflight_payload(),
    )
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_api_accepts_preflight_with_valid_operator_token(api_client):
    response = api_client.post(
        "/api/v1/uploads/preflight",
        json=valid_preflight_payload(),
        headers={"Authorization": f"Bearer {issue_token()}"},
    )
    assert response.status_code == 200
    assert response.json()["accepted"] is True


def test_health_endpoint_remains_public(api_client):
    response = api_client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
