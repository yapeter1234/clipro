import asyncio
from uuid import UUID

from fastapi.testclient import TestClient

from services.api.app.auth import OPERATOR_USER_ID, get_current_user
from services.api.app.main import app


def test_public_identity_is_shared_internal_workspace_identity():
    user = asyncio.run(get_current_user())
    assert user.user_id == UUID("00000000-0000-4000-8000-000000000001")
    assert OPERATOR_USER_ID == user.user_id


def test_api_accepts_preflight_without_password_or_bearer_token():
    payload = {
        "original_filename": "authorized-clip.mp4",
        "content_type": "video/mp4",
        "file_size_bytes": 25_000_000,
        "platform": "upload",
        "source_kind": "uploaded_video",
        "acquisition_mode": "authorized_source_file",
        "permission_confirmed": True,
        "rights_status": "creator_authorized",
    }
    with TestClient(app) as client:
        response = client.post("/api/v1/uploads/preflight", json=payload)
    assert response.status_code == 200
    assert response.json()["accepted"] is True


def test_health_endpoint_remains_public():
    with TestClient(app) as client:
        response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "clipro-api"}
