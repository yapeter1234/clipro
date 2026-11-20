"""Clipro serverless media workers.

Deploy with the Clipro worker Secret configured. Functions download only
server-approved object keys from the private R2 bucket; they never fetch
platform URLs supplied by users.
"""
from __future__ import annotations

import asyncio
import json
import os
import tempfile
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import asyncpg
import boto3
import modal
from botocore.config import Config

from services.worker.app.media_probe import (
    create_thumbnail,
    probe_media,
    sha256_file,
)

APP_NAME = "clipro-workers"
SECRET_NAME = "clipro-worker-secrets"
THUMBNAIL_ROOT = "assets"

app = modal.App(APP_NAME)
image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("ffmpeg")
    .pip_install("asyncpg>=0.30,<1", "boto3>=1.35,<2")
    .add_local_python_source("services")
)


def _database_url_and_ssl() -> tuple[str, str | bool]:
    """Accept Supabase's sslmode=require URL but pass TLS via asyncpg's ssl arg."""
    raw_url = os.environ["DATABASE_URL"]
    parts = urlsplit(raw_url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    ssl_mode = query.pop("sslmode", "require")
    clean_url = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
    ssl_value: str | bool = "require" if ssl_mode in {"require", "verify-ca", "verify-full"} else False
    return clean_url, ssl_value


def _r2_client():
    account_id = os.environ["R2_ACCOUNT_ID"]
    return boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        region_name="auto",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
            retries={"max_attempts": 4, "mode": "standard"},
        ),
    )


async def _set_job_failed(connection, job_id: str, asset_id: str, error: str) -> None:
    safe_error = (error or "Media probe failed.")[:500]
    await connection.execute(
        """UPDATE public.processing_jobs
           SET status='failed', progress=100, error_message=$2, completed_at=now(), updated_at=now()
           WHERE job_id=$1""",
        job_id,
        safe_error,
    )
    await connection.execute(
        "UPDATE public.media_assets SET state='failed' WHERE asset_id=$1",
        asset_id,
    )


@app.function(
    image=image,
    secrets=[modal.Secret.from_name(SECRET_NAME)],
    cpu=2,
    memory=4096,
    ephemeral_disk=50 * 1024,
    timeout=1800,
    retries=1,
    max_containers=2,
    scaledown_window=60,
)
def probe_asset(job_id: str, asset_id: str, workspace_id: str) -> dict:
    """Download one authorized R2 source, probe it and create a thumbnail."""
    async def run() -> dict:
        dsn, ssl_value = _database_url_and_ssl()
        connection = await asyncpg.connect(dsn=dsn, ssl=ssl_value)
        try:
            row = await connection.fetchrow(
                """SELECT asset_id, workspace_id, storage_key, original_filename
                   FROM public.media_assets
                   WHERE asset_id=$1 AND workspace_id=$2""",
                asset_id,
                workspace_id,
            )
            if row is None:
                raise RuntimeError("The media asset does not exist in this workspace.")

            await connection.execute(
                """UPDATE public.processing_jobs
                   SET status='running', progress=5, started_at=coalesce(started_at, now()),
                       attempt_count=attempt_count+1, updated_at=now()
                   WHERE job_id=$1 AND asset_id=$2 AND workspace_id=$3""",
                job_id,
                asset_id,
                workspace_id,
            )
            await connection.execute(
                "UPDATE public.media_assets SET state='probing' WHERE asset_id=$1",
                asset_id,
            )

            bucket = os.environ["R2_BUCKET_NAME"]
            storage_key = str(row["storage_key"])
            s3 = _r2_client()

            with tempfile.TemporaryDirectory(prefix="clipro-probe-") as temp_dir:
                local_source = Path(temp_dir) / "source-video"
                local_thumbnail = Path(temp_dir) / "thumbnail.jpg"
                s3.download_file(bucket, storage_key, str(local_source))

                probe = probe_media(local_source)
                checksum = sha256_file(local_source)
                create_thumbnail(
                    local_source,
                    local_thumbnail,
                    duration_ms=probe["duration_ms"],
                )

                thumbnail_key = (
                    f"workspaces/{workspace_id}/{THUMBNAIL_ROOT}/{asset_id}/thumbnail.jpg"
                )
                s3.upload_file(
                    str(local_thumbnail),
                    bucket,
                    thumbnail_key,
                    ExtraArgs={
                        "ContentType": "image/jpeg",
                        "Metadata": {
                            "clipro-asset-id": asset_id,
                            "clipro-workspace-id": workspace_id,
                        },
                    },
                )

            probe["checksum_sha256"] = checksum
            probe["thumbnail_key"] = thumbnail_key
            encoded_probe = json.dumps(probe)

            await connection.execute(
                """UPDATE public.media_assets
                   SET state='ready',
                       duration_ms=$2,
                       width=$3,
                       height=$4,
                       frame_rate_num=$5,
                       frame_rate_den=$6,
                       video_codec=$7,
                       audio_codec=$8,
                       checksum_sha256=$9,
                       probe_metadata=$10::jsonb,
                       thumbnail_key=$11
                   WHERE asset_id=$1 AND workspace_id=$12""",
                asset_id,
                probe["duration_ms"],
                probe["width"],
                probe["height"],
                probe["frame_rate_num"],
                probe["frame_rate_den"],
                probe["video_codec"],
                probe["audio_codec"],
                checksum,
                encoded_probe,
                thumbnail_key,
                workspace_id,
            )
            await connection.execute(
                """UPDATE public.processing_jobs
                   SET status='succeeded', progress=100, result_json=$2::jsonb,
                       error_message=NULL, completed_at=now(), updated_at=now()
                   WHERE job_id=$1""",
                job_id,
                encoded_probe,
            )
            return {
                "job_id": job_id,
                "asset_id": asset_id,
                "status": "ready",
                "probe": probe,
            }
        except Exception as exc:
            try:
                await _set_job_failed(connection, job_id, asset_id, str(exc))
            except Exception:
                pass
            raise
        finally:
            await connection.close()

    return asyncio.run(run())
