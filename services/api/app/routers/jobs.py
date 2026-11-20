"""Workspace-authorized processing-job status and retry endpoints."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from starlette.concurrency import run_in_threadpool

from ..auth import CurrentUser, get_current_user
from ..database import get_pool, require_workspace_membership
from ..modal_dispatch import spawn_media_probe
from ..settings import get_settings

router = APIRouter(prefix="/api/v1/jobs", tags=["processing jobs"])


async def _fetch_job(job_id: UUID) -> dict:
    pool = await get_pool()
    async with pool.acquire() as connection:
        row = await connection.fetchrow(
            """SELECT job_id, workspace_id, asset_id, job_type, status, progress,
                      attempt_count, modal_call_id, dispatch_error, error_message,
                      result_json, created_at, updated_at, started_at, completed_at
               FROM public.processing_jobs WHERE job_id=$1""",
            job_id,
        )
    if row is None:
        raise HTTPException(status_code=404, detail="Processing job was not found.")
    return dict(row)


def _serialize_job(row: dict) -> dict:
    import json
    result = row.get("result_json")
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except json.JSONDecodeError:
            result = None
    return {
        "job_id": str(row["job_id"]),
        "asset_id": str(row["asset_id"]),
        "job_type": row["job_type"],
        "status": row["status"],
        "progress": row["progress"],
        "attempt_count": row["attempt_count"],
        "dispatch_error": row["dispatch_error"],
        "error_message": row["error_message"],
        "result": result,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "started_at": row["started_at"],
        "completed_at": row["completed_at"],
    }


@router.get("/{job_id}")
async def get_job(job_id: UUID, user: CurrentUser = Depends(get_current_user)):
    row = await _fetch_job(job_id)
    await require_workspace_membership(row["workspace_id"], user.user_id, write=False)
    return _serialize_job(row)


@router.post("/{job_id}/dispatch")
async def retry_job_dispatch(job_id: UUID, user: CurrentUser = Depends(get_current_user)):
    row = await _fetch_job(job_id)
    await require_workspace_membership(row["workspace_id"], user.user_id, write=True)

    if row["job_type"] != "media_probe":
        raise HTTPException(status_code=409, detail="This job type cannot be dispatched here.")
    if row["status"] in {"running", "succeeded"}:
        return _serialize_job(row)
    if not get_settings().clipro_modal_dispatch_enabled:
        raise HTTPException(status_code=503, detail="Modal worker dispatch is not enabled for this API.")

    try:
        call_id = await run_in_threadpool(
            spawn_media_probe,
            job_id=str(row["job_id"]),
            asset_id=str(row["asset_id"]),
            workspace_id=str(row["workspace_id"]),
        )
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="The Modal worker could not be started. Confirm that the worker app is deployed and API credentials are configured.",
        ) from None

    pool = await get_pool()
    async with pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                """UPDATE public.processing_jobs
                   SET status='queued', progress=0, modal_call_id=$2,
                       dispatch_error=NULL, error_message=NULL, updated_at=now()
                   WHERE job_id=$1""",
                job_id,
                call_id,
            )
            await connection.execute(
                "UPDATE public.media_assets SET state='probing' WHERE asset_id=$1",
                row["asset_id"],
            )

    return _serialize_job(await _fetch_job(job_id))
