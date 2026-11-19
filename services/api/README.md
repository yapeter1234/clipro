# Control API

The FastAPI control plane should be stateless where possible; durable state belongs in the database and media workers.

## API contract (planned)

### Monitoring
- `POST /api/v1/monitors` — create one monitor session.
- `GET /api/v1/monitors/{monitor_id}` — retrieve health/status.
- `POST /api/v1/monitors/{monitor_id}/stop` — stop monitor.
- `POST /api/v1/webhooks/twitch` — verified Twitch EventSub callback.
- `POST /api/v1/webhooks/kick` — verified Kick webhook.
- `POST /api/v1/webhooks/youtube` — only if a supported YouTube notification integration is configured.

### Candidates and renders
- `GET /api/v1/candidates` — list candidate moments.
- `GET /api/v1/candidates/{candidate_id}` — details and evidence.
- `POST /api/v1/candidates/{candidate_id}/render` — create or regenerate a render.
- `GET /api/v1/renders/{render_id}` — status, asset links and QA result.
- `POST /api/v1/renders/{render_id}/approve` — bind human approval to this exact render/checksum.
- `POST /api/v1/renders/{render_id}/reject` — reject render.
- `GET /api/v1/renders/{render_id}/download` — authorized short-lived download.

### Publishing
Not implemented in MVP. A future publish endpoint must verify workspace ownership, campaign requirements, rights/authorization and an approval record for the exact render version. Any modification creates a new version requiring new approval.

## State model

Monitor: `created -> starting -> monitoring -> stopping -> stopped | failed`.

Candidate: `detected -> analyzing -> selected | discarded`.

Render: `queued -> rendering -> qa_passed -> pending_approval -> approved | rejected`.

Never use client-supplied state transitions as authority. The backend validates every transition and persists an audit event.

## Security

All non-webhook APIs require workspace authentication and authorization. Webhooks require provider signature verification. Ingest is separately authenticated and rate-limited. The API must not proxy arbitrary user-supplied URLs or invoke shell commands using untrusted strings.
