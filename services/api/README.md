# Control API

The FastAPI control plane owns source validation, multipart session orchestration and asset state. Durable metadata lives in Postgres; source media lives in private R2.

## Upload endpoints

- GET /healthz
- POST /api/v1/uploads/preflight — validates acquisition method, rights confirmation, declared type and file size.
- POST /api/v1/uploads — creates the R2 multipart session and durable Clipro asset/session records.
- POST /api/v1/uploads/sign-request — verifies the caller and upload session, then presigns one Uppy 6 S3 operation.
- POST /api/v1/uploads/finalize — verifies the completed object in R2 and records its asset as uploaded.
- POST /api/v1/uploads/abort — server-side abort for an active multipart session.
- GET /api/v1/uploads/asset/{asset_id}

Uppy 6.3 moved custom S3 signing to a single signRequest callback. The client asks this endpoint to sign ListParts, UploadPart, CompleteMultipartUpload and AbortMultipartUpload. The initial multipart upload is created by the API before Uppy is started; the browser attaches that upload ID to the Uppy file's resumable state.

Mutating endpoints require a valid Supabase access token, owner/admin/editor workspace membership and the original uploader identity. JWT verification supports asymmetric ES256 or RS256 keys.

## Required setup

1. Apply supabase/migrations/202611190001_m1_media_uploads.sql.
2. Create a private R2 bucket and a bucket-scoped API token.
3. Configure R2 CORS for the exact Clipro web origin. Allow PUT and expose the ETag response header so the browser can read uploaded part identifiers. Allow only the headers required by signed uploads.
4. Configure variables from services/api/.env.example as secure service environment variables or Modal Secrets.
5. Set CLIPRO_WEB_ORIGINS to comma-separated allowed web origins.
6. Add the local and production app origins, including /auth/callback, to Supabase Auth's redirect URL allowlist.
7. Configure an asymmetric Supabase JWT signing key (ES256 or RS256).

Do not expose database or R2 credentials in Next.js public environment variables. Keep the R2 bucket private. Configure a bucket lifecycle rule to abort incomplete multipart uploads after the upload-session TTL.

## Upload states

Upload: uploading -> completed | aborted | expired | failed.
Asset: uploading -> uploaded -> probing -> ready | rejected | failed.

The finalize endpoint verifies the R2 object size and expected asset metadata. ffprobe must still validate actual media bytes before analysis.

## Security and publication

Source URLs are references only and are never fetched. No social publishing credentials or endpoint exist. Final review and publication remain manual.
