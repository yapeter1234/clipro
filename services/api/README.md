# Control API

The FastAPI control plane is stateless where possible; durable state belongs in Postgres and media workers.

## Implemented

- GET /healthz — service health.
- POST /api/v1/uploads/preflight — validates source acquisition, rights confirmation, declared media type and upload size.
- POST /api/v1/uploads — authenticated R2 multipart session creation and durable asset/session records.
- POST /api/v1/uploads/sign-part — returns a short-lived presigned R2 UploadPart URL.
- POST /api/v1/uploads/list-parts — lists uploaded parts for resume.
- POST /api/v1/uploads/complete — compares client ETags with the R2 inventory, completes the multipart upload and checks final object size.
- POST /api/v1/uploads/abort — aborts an active multipart session.
- GET /api/v1/uploads/asset/{asset_id} — returns workspace-authorized upload status.

All mutating upload endpoints require a valid Supabase access token, an owner/admin/editor workspace membership and the original uploader identity. Use asymmetric ES256 or RS256 Supabase JWT signing keys.

## Required setup

1. Apply supabase/migrations/202611190001_m1_media_uploads.sql.
2. Create a private R2 bucket for Clipro.
3. Create an R2 API token scoped only to that bucket, with object read/write permissions needed by the uploader.
4. Configure the environment from services/api/.env.example as secure server-side environment variables or Modal Secrets.
5. Configure R2 CORS to allow PUT from the exact Clipro web origin and expose the ETag response header. Allow only the required methods and headers.
6. Confirm the Supabase project's JWT signing key is asymmetric ES256 or RS256. This implementation does not support legacy HS256 verification.

Do not expose database or R2 credentials in Next.js public environment variables. Do not enable a public bucket.

## Upload states

Upload: uploading -> completed | aborted | expired | failed.
Asset: uploading -> uploaded -> probing -> ready | rejected | failed.

The multipart API stores an upload session in Postgres. It does not fetch a source URL, probe the media or dispatch a worker yet. A successful multipart completion proves the declared object size was uploaded; ffprobe must still validate the actual media bytes before analysis.

## Security and publication

No social publishing credentials or publishing endpoint exist. Final review and publication remain manual.
