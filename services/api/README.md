# Control API

The FastAPI control plane should be stateless where possible; durable state belongs in Postgres and media workers.

## Current implementation

- GET /healthz — service health.
- POST /api/v1/uploads/preflight — validates source method, permission/rights confirmation, declared file extension/MIME and upload size before transfer.

The preflight endpoint does not store bytes, create a multipart upload, probe media or start a worker. Those are the next M1 slices. Do not expose this API publicly until the authentication boundary is configured.

## Planned API contract

### Uploads and assets
- POST /api/v1/uploads — create a private object-store multipart upload and persist its Clipro asset record.
- POST /api/v1/uploads/{upload_id}/parts/{part_number}/sign — return a short-lived upload-part URL.
- POST /api/v1/uploads/{upload_id}/complete — complete multipart upload and verify object metadata.
- POST /api/v1/uploads/{upload_id}/abort — abort an incomplete upload.
- GET /api/v1/uploads/{upload_id} — retrieve upload state.
- POST /api/v1/assets/{asset_id}/probe — enqueue ffprobe/proxy generation.
- GET /api/v1/assets/{asset_id} — inspect media metadata and readiness.

### Jobs and renders
- POST /api/v1/jobs — enqueue analysis/edit job for a validated asset.
- GET /api/v1/jobs/{job_id} — get status and progress.
- GET /api/v1/renders/{render_id} — status, asset links and QA result.
- POST /api/v1/renders/{render_id}/approve — bind human approval to this exact render/checksum.
- POST /api/v1/renders/{render_id}/reject — reject render.
- GET /api/v1/renders/{render_id}/download — authorized short-lived download.

## Monitoring

- POST /api/v1/monitors — create a monitor session.
- GET /api/v1/monitors/{monitor_id} — retrieve health/status.
- POST /api/v1/monitors/{monitor_id}/stop — stop monitor.
- POST /api/v1/webhooks/twitch — verified Twitch EventSub callback.
- POST /api/v1/webhooks/kick — verified Kick webhook.
- POST /api/v1/webhooks/youtube — only if a supported YouTube notification integration is configured.

Monitoring is not part of the manual-capture MVP.

## Publishing

Not implemented in MVP. A future publish endpoint must verify workspace ownership, campaign requirements, rights/authorization and an approval record for the exact render version. Any modification creates a new version requiring new approval.

## State model

Upload: preflighted -> uploading -> uploaded -> probing -> ready | rejected | failed.
Job: queued -> running -> succeeded | failed.
Render: queued -> rendering -> qa_passed -> pending_approval -> approved | rejected.

Never use client-supplied state transitions as authority. The backend validates every transition and persists an audit event.

## Security

All non-webhook APIs require workspace authentication and authorization. Webhooks require provider signature verification. Upload signing is separately authenticated and rate-limited. The API must not proxy arbitrary user-supplied URLs or invoke shell commands using untrusted strings.
