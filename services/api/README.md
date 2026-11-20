# Control API

The FastAPI control plane owns source validation, multipart orchestration, durable job state and media-processing APIs. Postgres stores metadata; private R2 stores media.

## Current implementation status

The current M1 upload implementation still verifies Supabase access tokens and checks workspace membership. This is legacy scaffolding. **Do not deploy it as an unauthenticated API and do not assume that removing the browser login screen makes it private.**

The private single-operator refactor must:
- replace Supabase Auth/user/workspace authorization with a private access-layer identity check;
- verify Cloudflare Access JWTs (or an equivalent trusted identity assertion) server-side on every protected route;
- remove workspace membership joins and user ownership fields from the active data model;
- retain server-side authorization for asset IDs, upload sessions, jobs and signed downloads;
- keep R2 private and all credentials server-side.

CORS is not authentication. A browser-shared static API key is not an acceptable substitute.

## Upload endpoints

- GET /healthz
- POST /api/v1/uploads/preflight
- POST /api/v1/uploads — creates a private R2 multipart upload and persistent asset/session.
- POST /api/v1/uploads/sign-request — authorizes and presigns an Uppy 6 S3 operation.
- POST /api/v1/uploads/finalize — verifies the R2 object and creates a durable media-probe job.
- POST /api/v1/uploads/abort
- GET /api/v1/uploads/asset/{asset_id}

## Processing jobs

- GET /api/v1/jobs/{job_id} — protected job status/progress/result.
- POST /api/v1/jobs/{job_id}/dispatch — retry dispatch after Modal has been deployed/configured.

## Required setup after the private refactor

1. Create a private Postgres database/schema and apply the single-operator migrations.
2. Create a private R2 bucket and bucket-scoped API token.
3. Configure R2 CORS for the exact private dashboard origin.
4. Configure the private access layer for both dashboard and API hostnames, allowing only the operator.
5. Configure API/worker environment variables as secure service secrets.
6. Deploy the Modal worker and API.
7. Enable dispatch only after end-to-end tests pass.

Do not expose database, Modal or R2 credentials in Next.js public environment variables. Keep the R2 bucket private.

## Upload and job states

Upload: uploading -> completed | aborted | expired | failed.
Asset: uploading -> uploaded -> probing -> ready | rejected | failed.
Job: queued -> running -> succeeded | failed.

Multipart completion proves the declared object size was uploaded. The Modal worker must validate actual file bytes before analysis.

No automatic social publishing endpoint or credentials are in scope.
