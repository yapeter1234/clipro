# Control API

The FastAPI control plane is stateless where possible; durable state belongs in Postgres and media workers.

## Implemented

- GET /healthz
- POST /api/v1/uploads/preflight
- POST /api/v1/uploads — authenticated R2 multipart session creation and durable asset/session records
- POST /api/v1/uploads/sign-part — short-lived presigned R2 UploadPart URL
- POST /api/v1/uploads/list-parts — uploaded part inventory for resume
- POST /api/v1/uploads/complete — validates R2 ETags/part numbers and final object size
- POST /api/v1/uploads/abort
- GET /api/v1/uploads/asset/{asset_id}

Mutating endpoints require a valid Supabase access token, an owner/admin/editor workspace membership and the original uploader identity. JWT verification supports asymmetric ES256 or RS256 signing keys.

## Required setup

1. Apply supabase/migrations/202611190001_m1_media_uploads.sql.
2. Create a private R2 bucket and a bucket-scoped API token.
3. Configure R2 CORS for the exact Clipro web origin. Allow PUT, allow the headers used by signed uploads, and expose the ETag response header so the browser can report multipart parts.
4. Configure services/api/.env.example as secure service environment variables or Modal Secrets.
5. Add the deployed web origin to CLIPRO_WEB_ORIGINS.
6. Add the local and production origins, including /auth/callback, to Supabase Auth redirect URL allowlist.
7. Configure an asymmetric Supabase JWT signing key (ES256 or RS256).

Do not expose database or R2 credentials in Next.js public environment variables. Keep the R2 bucket private.

## Upload states

Upload: uploading -> completed | aborted | expired | failed.
Asset: uploading -> uploaded -> probing -> ready | rejected | failed.

Multipart completion proves the declared object size was uploaded. ffprobe must still validate media bytes before analysis.

## Security and publication

Source URLs are references only and are never fetched. No social publishing credentials or publishing endpoint exist. Final review and publication remain manual.
