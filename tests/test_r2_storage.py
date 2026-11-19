from uuid import UUID

import pytest
from fastapi import HTTPException

from services.api.app.routers.uploads import CompletedPart, _validate_client_parts
from services.api.app.r2_storage import build_storage_key, sign_multipart_request


def test_storage_key_is_server_generated_and_uses_safe_extension() -> None:
    workspace_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    asset_id = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
    key = build_storage_key(workspace_id, asset_id, "../../my clip.MP4")
    assert key == (
        "workspaces/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/"
        "sources/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb/original.mp4"
    )


def test_invalid_extension_is_replaced() -> None:
    workspace_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    asset_id = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
    assert build_storage_key(workspace_id, asset_id, "file.bad-extension!").endswith("/original.bin")


def test_part_list_must_match_r2_inventory() -> None:
    client_parts = [
        CompletedPart.model_validate({"PartNumber": 1, "ETag": '"etag-1"'}),
        CompletedPart.model_validate({"PartNumber": 2, "ETag": '"etag-2"'}),
    ]
    server_parts = [
        {"PartNumber": 1, "ETag": '"etag-1"', "Size": 5 * 1024 * 1024},
        {"PartNumber": 2, "ETag": '"etag-2"', "Size": 120},
    ]
    assert _validate_client_parts(client_parts, server_parts) == [
        {"PartNumber": 1, "ETag": '"etag-1"'},
        {"PartNumber": 2, "ETag": '"etag-2"'},
    ]


def test_part_list_rejects_forged_etag() -> None:
    client_parts = [CompletedPart.model_validate({"PartNumber": 1, "ETag": '"fake"'})]
    server_parts = [{"PartNumber": 1, "ETag": '"real"', "Size": 100}]
    with pytest.raises(HTTPException) as exc:
        _validate_client_parts(client_parts, server_parts)
    assert exc.value.status_code == 400


def test_part_numbers_must_be_contiguous() -> None:
    client_parts = [
        CompletedPart.model_validate({"PartNumber": 1, "ETag": '"etag-1"'}),
        CompletedPart.model_validate({"PartNumber": 3, "ETag": '"etag-3"'}),
    ]
    server_parts = [
        {"PartNumber": 1, "ETag": '"etag-1"', "Size": 5},
        {"PartNumber": 3, "ETag": '"etag-3"', "Size": 5},
    ]
    with pytest.raises(HTTPException) as exc:
        _validate_client_parts(client_parts, server_parts)
    assert exc.value.status_code == 400


def test_sign_multipart_request_uses_presigned_part_operation(monkeypatch) -> None:
    class FakeS3:
        def __init__(self):
            self.call = None

        def generate_presigned_url(self, **kwargs):
            self.call = kwargs
            return "https://r2.test/presigned"

    from services.api.app import r2_storage
    fake = FakeS3()
    monkeypatch.setattr(r2_storage, "get_s3_client", lambda: fake)
    monkeypatch.setattr(r2_storage, "get_bucket_name", lambda: "clipro-private")
    result = sign_multipart_request(
        method="PUT", key="workspace/source/video.mp4", upload_id="upload-123", part_number=4
    )
    assert result == "https://r2.test/presigned"
    assert fake.call["ClientMethod"] == "upload_part"
    assert fake.call["Params"]["UploadId"] == "upload-123"
    assert fake.call["Params"]["PartNumber"] == 4
    assert fake.call["HttpMethod"] == "PUT"


def test_sign_multipart_request_rejects_missing_part_number() -> None:
    with pytest.raises(ValueError, match="part number"):
        sign_multipart_request(method="PUT", key="clip.mp4", upload_id="upload-123")
