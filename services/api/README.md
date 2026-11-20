# Control API

The FastAPI control plane owns source validation, multipart orchestration, durable job state and review/download APIs. Postgres stores metadata; private R2 stores media.

## Upload endpoints

- GET /healthz
- POST /api/v1/uploads/preflight
- POST /api/v1/uploads — creates a private R2 multipart upload and persistent Clipro asset/session.
- POST /api/v1/uploads/sign-request — verifies session ownership and presigns an Uppy 6 S3 operation.
- POST /api/v1/uploads/finalize — verifies the R2 object and creates a durable media-probe job.
- POST /api/v1/uploads/abort
- GET /api/v1/uploads/asset/{asset_id} — returns actual probe metadata and latest job state.

## Processing jobs

- GET /api/v1/jobs/{job_id} — authenticated status/progress/result.
- POST /api/v1/jobs/{job_id}/dispatch — retry dispatch after Modal has been deployed/configured.

The finalize endpoint does not fail an already completed upload when Modal is unavailable. It retains the job in queued state and records the dispatch issue; an owner/editor can retry after configuration.

## Required setup

1. Apply both migrations in supabase/migrations in numeric order.
2. Create a private R2 bucket and a bucket-scoped API token.
3. Configure R2 CORS for the exact Clipro web origin; allow PUT and expose ETag.
4. Configure variables from services/api/.env.example as secure service environment variables.
5. Deploy infra/modal/clipro_workers.py after creating the Modal Secret described in infra/modal/README.md.
6. Set CLIPRO_MODAL_DISPATCH_ENABLED=true and add Modal API credentials to the API environment (MODAL_TOKEN_ID and MODAL_TOKEN_SECRET).
7. Set DATABASE_SSL=true for Supabase Postgres and add exact web origins to CLIPRO_WEB_ORIGINS and Supabase Auth redirects.

Do not expose database, Modal or R2 credentials in Next.js public environment variables. Keep the R2 bucket private.

## Upload and job states

Upload: uploading -> completed | aborted | expired | failed.
Asset: uploading -> uploaded -> probing -> ready | rejected | failed.
Job: queued -> running -> succeeded | failed.

Multipart completion proves the declared object size was uploaded. The Modal ffprobe worker still validates the actual file bytes before analysis.

No automatic social publishing endpoint or credentials exist.
