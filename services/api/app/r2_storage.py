"""Cloudflare R2 S3-compatible multipart storage adapter."""
from __future__ import annotations

from functools import lru_cache
from typing import Any
from uuid import UUID

import boto3
from botocore.config import Config

from .settings import get_settings


class StorageNotConfigured(RuntimeError):
    pass


def is_r2_configured() -> bool:
    settings = get_settings()
    return all((settings.r2_account_id, settings.r2_access_key_id, settings.r2_secret_access_key, settings.r2_bucket_name))


@lru_cache(maxsize=1)
def get_s3_client():
    settings = get_settings()
    if not is_r2_configured():
        raise StorageNotConfigured("Cloudflare R2 is not configured.")
    return boto3.client(
        "s3",
        endpoint_url=f"https://{settings.r2_account_id}.r2.cloudflarestorage.com",
        region_name="auto",
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
            retries={"max_attempts": 4, "mode": "standard"},
        ),
    )


def get_bucket_name() -> str:
    bucket = get_settings().r2_bucket_name
    if not bucket:
        raise StorageNotConfigured("R2 bucket name is not configured.")
    return bucket


def build_storage_key(workspace_id: UUID, asset_id: UUID, filename: str) -> str:
    safe_name = filename.replace("\\", "/").rsplit("/", 1)[-1]
    extension = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else "bin"
    if not extension.isalnum() or len(extension) > 10:
        extension = "bin"
    return f"workspaces/{workspace_id}/sources/{asset_id}/original.{extension}"


def create_multipart_upload(*, key: str, content_type: str, asset_id: UUID, workspace_id: UUID) -> str:
    result = get_s3_client().create_multipart_upload(
        Bucket=get_bucket_name(),
        Key=key,
        ContentType=content_type,
        Metadata={"clipro-asset-id": str(asset_id), "clipro-workspace-id": str(workspace_id)},
    )
    upload_id = result.get("UploadId")
    if not upload_id:
        raise RuntimeError("R2 did not return a multipart upload ID.")
    return str(upload_id)


def sign_multipart_request(
    *, method: str, key: str, upload_id: str, part_number: int | None = None
) -> str:
    """Presign one R2 multipart operation for Uppy 6's signRequest callback."""
    client_method_by_request = {
        ("GET", False): ("list_parts", "GET"),
        ("PUT", True): ("upload_part", "PUT"),
        ("POST", False): ("complete_multipart_upload", "POST"),
        ("DELETE", False): ("abort_multipart_upload", "DELETE"),
    }
    normalized_method = method.upper()
    is_part = normalized_method == "PUT"
    operation = client_method_by_request.get((normalized_method, is_part))
    if operation is None:
        raise ValueError("Unsupported S3 multipart operation.")
    client_method, http_method = operation

    if client_method == "upload_part":
        if part_number is None or not 1 <= part_number <= 10000:
            raise ValueError("A valid multipart part number is required.")
    elif part_number is not None:
        raise ValueError("part_number is only valid for upload_part.")

    params: dict[str, Any] = {
        "Bucket": get_bucket_name(),
        "Key": key,
        "UploadId": upload_id,
    }
    if client_method == "upload_part":
        params["PartNumber"] = part_number

    return get_s3_client().generate_presigned_url(
        ClientMethod=client_method,
        Params=params,
        ExpiresIn=get_settings().upload_part_url_ttl_seconds,
        HttpMethod=http_method,
    )


def sign_part(*, key: str, upload_id: str, part_number: int) -> str:
    return sign_multipart_request(method="PUT", key=key, upload_id=upload_id, part_number=part_number)


def list_all_parts(*, key: str, upload_id: str) -> list[dict[str, Any]]:
    client = get_s3_client()
    parts: list[dict[str, Any]] = []
    marker: int | None = None
    while True:
        params: dict[str, Any] = {"Bucket": get_bucket_name(), "Key": key, "UploadId": upload_id, "MaxParts": 1000}
        if marker is not None:
            params["PartNumberMarker"] = marker
        response = client.list_parts(**params)
        parts.extend(response.get("Parts", []))
        if not response.get("IsTruncated"):
            break
        marker = response.get("NextPartNumberMarker")
        if marker is None:
            raise RuntimeError("R2 returned truncated parts without a marker.")
    return sorted(parts, key=lambda part: int(part["PartNumber"]))


def complete_multipart_upload(*, key: str, upload_id: str, parts: list[dict[str, Any]]) -> dict[str, Any]:
    return get_s3_client().complete_multipart_upload(
        Bucket=get_bucket_name(), Key=key, UploadId=upload_id, MultipartUpload={"Parts": parts}
    )


def abort_multipart_upload(*, key: str, upload_id: str) -> None:
    get_s3_client().abort_multipart_upload(Bucket=get_bucket_name(), Key=key, UploadId=upload_id)


def head_object(*, key: str) -> dict[str, Any]:
    return get_s3_client().head_object(Bucket=get_bucket_name(), Key=key)
