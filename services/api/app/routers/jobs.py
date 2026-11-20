"""Workspace-authorized processing-job status and retry endpoints."""
from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from starlette.concurrency import run_in_threadpool

from ..auth import CurrentUser, get_current_user
from ..database import get_pool, require_workspace_membership
from ..modal_dispatch import spawn_highlight_analysis, spawn_media_probe
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

    if row["job_type"] not in {"media_probe", "highlight_analysis"}:
        raise HTTPException(status_code=409, detail="This job type cannot be dispatched here.")
    if row["status"] in {"running", "succeeded"}:
        return _serialize_job(row)
    if not get_settings().clipro_modal_dispatch_enabled:
        raise HTTPException(status_code=503, detail="Modal worker dispatch is not enabled for this API.")

    try:
        dispatcher = spawn_media_probe if row["job_type"] == "media_probe" else spawn_highlight_analysis
        call_id = await run_in_threadpool(
            dispatcher,
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
            if row["job_type"] == "media_probe":
                await connection.execute(
                    "UPDATE public.media_assets SET state='probing' WHERE asset_id=$1",
                    row["asset_id"],
                )

    return _serialize_job(await _fetch_job(job_id))



@router.post("/assets/{asset_id}/analyze")
async def start_highlight_analysis(asset_id: UUID, user: CurrentUser = Depends(get_current_user)):
    """Create and dispatch an AI highlight-analysis job for a validated source."""
    pool = await get_pool()
    async with pool.acquire() as connection:
        asset = await connection.fetchrow(
            """SELECT asset_id, workspace_id, state, duration_ms
               FROM public.media_assets WHERE asset_id=$1""",
            asset_id,
        )
    if asset is None:
        raise HTTPException(status_code=404, detail="Media asset was not found.")
    await require_workspace_membership(asset["workspace_id"], user.user_id, write=True)
    if asset["state"] != "ready" or not asset["duration_ms"]:
        raise HTTPException(status_code=409, detail="The video must finish media validation before AI analysis.")

    async with pool.acquire() as connection:
        existing = await connection.fetchrow(
            """SELECT job_id, workspace_id, asset_id, job_type, status, progress,
                      attempt_count, modal_call_id, dispatch_error, error_message,
                      result_json, created_at, updated_at, started_at, completed_at
               FROM public.processing_jobs
               WHERE asset_id=$1 AND job_type='highlight_analysis'
                 AND status IN ('queued', 'running', 'succeeded')
               ORDER BY created_at DESC LIMIT 1""",
            asset_id,
        )
        if existing:
            return _serialize_job(dict(existing))
        job_id = uuid4()
        await connection.execute(
            """INSERT INTO public.processing_jobs
               (job_id, workspace_id, asset_id, job_type, status, progress)
               VALUES ($1,$2,$3,'highlight_analysis','queued',0)""",
            job_id, asset["workspace_id"], asset_id,
        )

    if not get_settings().clipro_modal_dispatch_enabled:
        async with pool.acquire() as connection:
            await connection.execute(
                """UPDATE public.processing_jobs SET dispatch_error=$2, updated_at=now()
                   WHERE job_id=$1""",
                job_id, "Deploy the Modal worker and enable CLIPRO_MODAL_DISPATCH_ENABLED to run AI analysis.",
            )
        return _serialize_job(await _fetch_job(job_id))

    try:
        call_id = await run_in_threadpool(
            spawn_highlight_analysis,
            job_id=str(job_id),
            asset_id=str(asset_id),
            workspace_id=str(asset["workspace_id"]),
        )
    except Exception as exc:
        async with pool.acquire() as connection:
            await connection.execute(
                """UPDATE public.processing_jobs SET dispatch_error=$2, updated_at=now()
                   WHERE job_id=$1""",
                job_id, f"Modal dispatch failed: {type(exc).__name__}",
            )
        return _serialize_job(await _fetch_job(job_id))

    async with pool.acquire() as connection:
        await connection.execute(
            """UPDATE public.processing_jobs SET modal_call_id=$2, dispatch_error=NULL,
               updated_at=now() WHERE job_id=$1""",
            job_id, call_id,
        )
    return _serialize_job(await _fetch_job(job_id))
