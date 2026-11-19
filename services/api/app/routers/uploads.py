"""Authenticated Uppy 6 / Cloudflare R2 multipart upload endpoints."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from starlette.concurrency import run_in_threadpool

from ..auth import CurrentUser, get_current_user
from ..database import fetch_upload_session, get_pool, require_workspace_membership
from ..ingestion import UploadPreflightRequest, validate_upload_preflight
from ..r2_storage import abort_multipart_upload, build_storage_key, create_multipart_upload, head_object, sign_multipart_request
from ..settings import get_settings

router = APIRouter(prefix="/api/v1/uploads", tags=["uploads"])


class UploadCreateRequest(UploadPreflightRequest):
    workspace_id: UUID


class UploadCreateResponse(BaseModel):
    asset_id: UUID
    upload_session_id: UUID
    upload_id: str
    key: str
    expires_at: datetime


class UploadPartsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    uploadId: str = Field(min_length=1, max_length=1024)
    key: str = Field(min_length=1, max_length=1024)


class S3SignRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    method: Literal["GET", "PUT", "POST", "DELETE"]
    key: str = Field(min_length=1, max_length=1024)
    uploadId: str = Field(min_length=1, max_length=1024)
    partNumber: int | None = Field(default=None, ge=1, le=10000)


class CompletedPart(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")
    part_number: int = Field(alias="PartNumber", ge=1, le=10000)
    etag: str = Field(alias="ETag", min_length=1, max_length=200)


def _validate_client_parts(client_parts: list[CompletedPart], server_parts: list[dict]) -> list[dict]:
    submitted = sorted(
        ({"PartNumber": item.part_number, "ETag": item.etag} for item in client_parts),
        key=lambda part: part["PartNumber"],
    )
    actual = [
        {"PartNumber": int(item["PartNumber"]), "ETag": str(item["ETag"])}
        for item in server_parts
    ]
    if not actual:
        raise HTTPException(status_code=400, detail="No upload parts were found in object storage.")
    if [part["PartNumber"] for part in submitted] != list(range(1, len(submitted) + 1)):
        raise HTTPException(status_code=400, detail="Upload part numbers must be contiguous and start at 1.")
    if submitted != actual:
        raise HTTPException(status_code=400, detail="Submitted parts do not match object storage.")
    return actual


async def _authorize_upload(upload_id: str, key: str, user: CurrentUser, *, write: bool = True) -> dict:
    session = await fetch_upload_session(upload_id, key)
    await require_workspace_membership(session["workspace_id"], user.user_id, write=write)
    if session["uploaded_by"] != user.user_id:
        raise HTTPException(status_code=403, detail="Only the uploader can manage this upload session.")
    if session["expires_at"] < datetime.now(timezone.utc) and session["status"] == "uploading":
        raise HTTPException(status_code=410, detail="Upload session expired.")
    return session


@router.post("", response_model=UploadCreateResponse)
async def create_upload(submission: UploadCreateRequest, user: CurrentUser = Depends(get_current_user)):
    payload = submission.model_dump(exclude={"workspace_id"})
    preflight = validate_upload_preflight(UploadPreflightRequest.model_validate(payload))
    if not preflight.accepted:
        raise HTTPException(status_code=422, detail={"errors": preflight.errors, "warnings": preflight.warnings})
    await require_workspace_membership(submission.workspace_id, user.user_id, write=True)

    settings = get_settings()
    if submission.file_size_bytes > settings.upload_max_file_size_bytes:
        raise HTTPException(status_code=413, detail="The file exceeds the configured upload limit.")

    asset_id = uuid4()
    session_id = uuid4()
    key = build_storage_key(submission.workspace_id, asset_id, submission.original_filename)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.upload_session_ttl_hours)
    storage_upload_id: str | None = None

    try:
        storage_upload_id = await run_in_threadpool(
            create_multipart_upload,
            key=key,
            content_type=submission.content_type,
            asset_id=asset_id,
            workspace_id=submission.workspace_id,
        )
        pool = await get_pool()
        async with pool.acquire() as connection:
            async with connection.transaction():
                await connection.execute(
                    """INSERT INTO public.media_assets (
                        asset_id, workspace_id, uploaded_by, streamer_id, campaign_id,
                        platform, source_kind, acquisition_mode, source_url,
                        original_filename, declared_mime_type, file_size_bytes,
                        storage_key, rights_status, rights_notes, permission_confirmed, state
                    ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,'uploading')""",
                    asset_id, submission.workspace_id, user.user_id,
                    submission.streamer_id, submission.campaign_id,
                    submission.platform.value, submission.source_kind.value,
                    submission.acquisition_mode.value,
                    str(submission.source_url) if submission.source_url else None,
                    submission.original_filename, submission.content_type,
                    submission.file_size_bytes, key, submission.rights_status.value,
                    submission.rights_notes, submission.permission_confirmed,
                )
                await connection.execute(
                    """INSERT INTO public.upload_sessions (
                        upload_session_id, asset_id, workspace_id, uploaded_by,
                        storage_upload_id, storage_key, status, expires_at
                    ) VALUES ($1,$2,$3,$4,$5,$6,'uploading',$7)""",
                    session_id, asset_id, submission.workspace_id, user.user_id,
                    storage_upload_id, key, expires_at,
                )
    except Exception:
        if storage_upload_id:
            try:
                await run_in_threadpool(abort_multipart_upload, key=key, upload_id=storage_upload_id)
            except Exception:
                pass
        raise

    return UploadCreateResponse(
        asset_id=asset_id,
        upload_session_id=session_id,
        upload_id=storage_upload_id,
        key=key,
        expires_at=expires_at,
    )


@router.post("/sign-request")
async def sign_s3_request(request: S3SignRequest, user: CurrentUser = Depends(get_current_user)):
    """Presign one Uppy 6 S3 operation after checking the durable upload session."""
    session = await _authorize_upload(request.uploadId, request.key, user)
    if session["status"] != "uploading":
        raise HTTPException(status_code=409, detail="Upload is not active.")
    url = await run_in_threadpool(
        sign_multipart_request,
        method=request.method,
        key=request.key,
        upload_id=request.uploadId,
        part_number=request.partNumber,
    )
    return {"url": url}


@router.post("/finalize")
async def finalize_upload(request: UploadPartsRequest, user: CurrentUser = Depends(get_current_user)):
    """Verify the completed object in R2 before marking its Clipro asset uploaded."""
    session = await _authorize_upload(request.uploadId, request.key, user)
    if session["status"] == "completed":
        return {"asset_id": str(session["asset_id"]), "status": "uploaded"}
    if session["status"] != "uploading":
        raise HTTPException(status_code=409, detail="Upload is not active.")

    object_info = await run_in_threadpool(head_object, key=request.key)
    total_bytes = int(object_info.get("ContentLength", -1))
    if total_bytes != session["file_size_bytes"]:
        raise HTTPException(status_code=400, detail="Stored object size does not match the declared file size.")
    metadata = object_info.get("Metadata") or {}
    if metadata.get("clipro-asset-id") != str(session["asset_id"]):
        raise HTTPException(status_code=400, detail="Stored object metadata does not match the expected asset.")

    pool = await get_pool()
    async with pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                """UPDATE public.upload_sessions
                   SET status='completed', completed_at=now(), updated_at=now()
                   WHERE upload_session_id=$1""",
                session["upload_session_id"],
            )
            await connection.execute(
                "UPDATE public.media_assets SET state='uploaded', completed_at=now() WHERE asset_id=$1",
                session["asset_id"],
            )
    return {"asset_id": str(session["asset_id"]), "status": "uploaded", "size_bytes": total_bytes}


@router.post("/abort")
async def abort_upload(request: UploadPartsRequest, user: CurrentUser = Depends(get_current_user)):
    session = await _authorize_upload(request.uploadId, request.key, user)
    if session["status"] == "completed":
        raise HTTPException(status_code=409, detail="Completed uploads cannot be aborted.")
    if session["status"] == "uploading":
        await run_in_threadpool(abort_multipart_upload, key=request.key, upload_id=request.uploadId)
        pool = await get_pool()
        async with pool.acquire() as connection:
            async with connection.transaction():
                await connection.execute(
                    "UPDATE public.upload_sessions SET status='aborted', updated_at=now() WHERE upload_session_id=$1",
                    session["upload_session_id"],
                )
                await connection.execute(
                    "UPDATE public.media_assets SET state='aborted' WHERE asset_id=$1",
                    session["asset_id"],
                )
    return {"asset_id": str(session["asset_id"]), "status": "aborted"}


@router.get("/asset/{asset_id}")
async def get_upload_status(asset_id: UUID, user: CurrentUser = Depends(get_current_user)):
    pool = await get_pool()
    async with pool.acquire() as connection:
        row = await connection.fetchrow(
            """SELECT asset_id, workspace_id, original_filename, declared_mime_type,
                      file_size_bytes, state, created_at, completed_at
               FROM public.media_assets WHERE asset_id=$1""",
            asset_id,
        )
    if row is None:
        raise HTTPException(status_code=404, detail="Asset was not found.")
    await require_workspace_membership(row["workspace_id"], user.user_id, write=False)
    return {
        "asset_id": str(row["asset_id"]),
        "filename": row["original_filename"],
        "content_type": row["declared_mime_type"],
        "size_bytes": row["file_size_bytes"],
        "status": row["state"],
        "created_at": row["created_at"],
        "completed_at": row["completed_at"],
    }
