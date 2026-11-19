# ADR-001: Media intake and storage

- Status: Accepted for the M1 prototype
- Date: 2026-11-19

## Context

Clipro must accept short native clips created manually from Twitch/Kick live streams and past broadcasts, creator/campaign-authorized source files, and ordinary uploaded videos for future manual editing. Large videos must upload reliably from a browser, without routing their bytes through the API. The same source and asset model must support multiple streamers and campaigns.

## Decision

1. Next.js is the browser studio.
2. Uppy + its AWS S3 plugin handles browser uploads using S3 multipart.
3. Cloudflare R2 stores original sources, proxies, thumbnails, timeline artifacts and final renders in private buckets.
4. Supabase Auth + Postgres stores identities, workspace membership, streamer/campaign profiles, asset metadata, job state, approvals and analytics evidence. RLS scopes rows by workspace.
5. FastAPI owns source validation, upload-session orchestration, job state and review/download APIs.
6. Modal runs short-lived media workers. Its Function API starts work asynchronously; the database remains the durable job ledger.
7. FFmpeg/ffprobe is the deterministic media foundation. PySceneDetect and ASR/VAD are analysis components. Remotion is optional pending license review.

## Upload sequence

1. The browser sends source metadata and declared file metadata to FastAPI.
2. FastAPI checks the source method, creator permission, file extension/MIME and configured size limit.
3. FastAPI creates a private R2 multipart upload and persists the Clipro asset/upload record.
4. Uppy requests short-lived signed URLs for each part and uploads file bytes directly to R2.
5. Uppy sends the completed part list to FastAPI. FastAPI completes the multipart upload and verifies the resulting object metadata.
6. FastAPI marks the asset as uploaded and schedules a Modal probe job.
7. The worker probes actual media, computes a checksum, creates a lightweight proxy and thumbnail, and records the result.
8. The dashboard presents the validated source and lets the user select a range or start analysis.

## Source metadata

Every upload should persist:
- workspace, streamer and optional campaign IDs;
- platform and source kind (live_stream, past_broadcast, uploaded_video);
- acquisition mode (viewer_native_clip_manual_download, authorized_source_file);
- source URL as a reference only, never as an instruction to fetch the video;
- original filename, declared MIME, byte size, actual probed streams and duration;
- R2 object key, checksum and asset status;
- permission confirmation, rights status, evidence/notes and retention policy;
- timestamps and an audit trail for state transitions.

A YouTube Clip URL is metadata only. It is not a media object and must never be fetched by the renderer. Custom editing requires an authorized uploaded source file.

## Upload states

preflighted -> uploading -> uploaded -> probing -> ready

Terminal error states are rejected and failed. Completion requests must be idempotent. An expired or aborted multipart upload cannot be marked uploaded. Object keys are generated server-side; a client never chooses a bucket path.

## Security requirements

- Private bucket; no public-read ACLs.
- Only short-lived signed upload-part URLs reach the browser.
- Never send R2 access keys to browser JavaScript.
- Scope object keys to the authenticated workspace.
- Enforce content-length limits, allowed extensions and declared MIME at preflight; then inspect real media with ffprobe.
- Treat filename and source URL as untrusted metadata. Never fetch arbitrary source URLs.
- Use a short-lived signed download URL for authorized preview/download.
- Persist rights status and authorization evidence before analysis.
- No auto-publishing endpoint or social-platform publishing credential in M1.

## M1 implementation boundary

The first code slice is the source/upload preflight contract. The next slices are R2 multipart signing/completion, the browser uploader and the ffprobe worker. Until those exist and cloud credentials are configured, the preflight response is not a claim that a file has been uploaded or stored.
