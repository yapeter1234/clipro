from uuid import UUID

from fastapi.testclient import TestClient

from services.api.app.auth import CurrentUser, get_current_user
from services.api.app.ingestion import MAX_UPLOAD_BYTES
from services.api.app.main import app

# These tests exercise upload metadata/rights policy, not bearer-token parsing.
# Keep the production dependency protected and explicitly provide the single
# operator identity to the test client.
app.dependency_overrides[get_current_user] = lambda: CurrentUser(
    user_id=UUID("00000000-0000-4000-8000-000000000001")
)
client = TestClient(app)


def valid_payload() -> dict:
    return {
        "original_filename": "diego-gta-clip.mp4",
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


def test_health_endpoint() -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_twitch_native_clip_preflight_is_accepted() -> None:
    response = client.post("/api/v1/uploads/preflight", json=valid_payload())
    assert response.status_code == 200
    body = response.json()
    assert body["accepted"] is True
    assert body["errors"] == []


def test_permission_must_be_confirmed() -> None:
    payload = valid_payload()
    payload["permission_confirmed"] = False
    response = client.post("/api/v1/uploads/preflight", json=payload)
    assert response.status_code == 200
    assert response.json()["accepted"] is False
    assert any("permission" in error.lower() for error in response.json()["errors"])


def test_pending_rights_status_is_blocked() -> None:
    payload = valid_payload()
    payload["rights_status"] = "pending_review"
    response = client.post("/api/v1/uploads/preflight", json=payload)
    assert response.status_code == 200
    assert response.json()["accepted"] is False
    assert any("rights status" in error.lower() for error in response.json()["errors"])


def test_youtube_clip_cannot_be_used_as_a_media_download() -> None:
    payload = valid_payload()
    payload.update(
        {
            "platform": "youtube",
            "source_url": "https://www.youtube.com/clip/example",
            "acquisition_mode": "viewer_native_clip_manual_download",
        }
    )
    response = client.post("/api/v1/uploads/preflight", json=payload)
    assert response.status_code == 200
    assert response.json()["accepted"] is False
    assert any("reference" in error.lower() for error in response.json()["errors"])


def test_generic_upload_requires_uploaded_video_source_kind() -> None:
    payload = valid_payload()
    payload.update(
        {
            "platform": "upload",
            "source_kind": "past_broadcast",
            "acquisition_mode": "authorized_source_file",
        }
    )
    response = client.post("/api/v1/uploads/preflight", json=payload)
    assert response.status_code == 200
    assert response.json()["accepted"] is False


def test_unsupported_file_extension_is_rejected() -> None:
    payload = valid_payload()
    payload.update(
        {
            "original_filename": "clip.exe",
            "content_type": "application/octet-stream",
        }
    )
    response = client.post("/api/v1/uploads/preflight", json=payload)
    assert response.status_code == 200
    assert response.json()["accepted"] is False
    assert any("Unsupported video format" in error for error in response.json()["errors"])


def test_file_size_limit_is_validated_by_schema() -> None:
    payload = valid_payload()
    payload["file_size_bytes"] = MAX_UPLOAD_BYTES + 1
    response = client.post("/api/v1/uploads/preflight", json=payload)
    assert response.status_code == 422


def test_campaign_must_reference_a_streamer() -> None:
    payload = valid_payload()
    payload["streamer_id"] = None
    response = client.post("/api/v1/uploads/preflight", json=payload)
    assert response.status_code == 200
    assert response.json()["accepted"] is False
