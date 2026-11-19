from uuid import UUID

import pytest
from fastapi import HTTPException

from services.api.app.routers.uploads import CompletedPart, _validate_client_parts
from services.api.app.r2_storage import build_storage_key


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
