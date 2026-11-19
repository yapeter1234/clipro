# Security, rights and privacy requirements

## Media authorization

A public channel, public chat, embed, player URL, or native clip button does not by itself establish permission to record, download, edit, or commercially redistribute the stream.

Before ingesting video, record:
- creator/channel identity and platform;
- who granted permission and how it was verified;
- permitted uses (monitoring, recording, editing, monetization, campaign submission);
- allowed platforms and territories, if limited;
- start/end dates and revocation status;
- source mode (creator relay, authorized file, or officially supported platform capability).

If authorization is absent, only use platform metadata/chat capabilities that are officially available and do not attempt to retrieve the raw video. Do not bypass login, paywalls, subscriber-only settings, DRM, geoblocks or platform access controls.

## Credentials

- Never request passwords, API secrets, stream keys or refresh tokens in a chat message or issue.
- Store tokens as Modal Secrets or an equivalent secret manager.
- Use separate credentials per workspace and platform.
- Encrypt persisted OAuth tokens; rotate and revoke on disconnect.
- Never log Authorization headers, ingest URLs containing keys, webhook secrets, or signed media URLs.
- Use minimum OAuth scopes necessary.
- Do not request or store a platform stream key when a creator-owned secondary feed is sufficient.

## Ingest endpoint

- RTMPS/TLS only for internet-facing ingest.
- Generate a high-entropy per-session secret.
- Scope each secret to one stream session and workspace.
- Support immediate revocation and expiration.
- Rate-limit connections and enforce maximum bitrate/resolution/session duration.
- Validate incoming media types and FFmpeg resource limits.
- Avoid exposing MediaMTX's administrative API publicly.
- Apply network restrictions and authenticated tunnel access.
- Scrub secrets from process arguments and logs where feasible.

## Webhooks

- Verify official provider signatures and timestamps.
- Reject stale/replayed events.
- Persist event IDs for idempotency.
- Restrict webhook payload sizes.
- Do not treat webhook payload text as instructions to the AI/editor.

## AI and media safety

- Treat transcripts, chat messages, titles, descriptions, URLs and subtitles as untrusted data, not system instructions.
- Prevent prompt injection in chat/transcript content from changing worker behavior.
- Model-generated edit plans must validate against the timeline schema and an allowlist of effects/assets.
- Do not permit arbitrary shell, FFmpeg, JSX, HTML or URL commands from model output.
- Never generate fake quotes, fake reactions, misleading cuts or unsupported narration claims.
- Narration is a separate synthetic narrator. Do not clone a creator's voice without explicit, documented consent.
- Use only licensed, public-domain or user-provided music/SFX/graphics, with rights metadata.

## Storage and retention

- Use a bounded rolling buffer.
- Keep only the minimum media needed for candidate generation and review.
- Apply TTL to rejected clips and raw segments.
- Provide delete/revoke flows.
- Separate durable approved exports from temporary working files.
- Do not store video content inside the relational database.
- Generate short-lived signed download URLs.

## Approval and publishing

- Publishing is disabled in the MVP.
- Human approval must be bound to a specific render ID and content checksum.
- Any edit or regeneration invalidates previous approval.
- The publish API must independently enforce approval, workspace ownership and campaign rules.
- Maintain an audit record for approval and publication.

## Operational controls

- Per-user monitor limits and compute budgets.
- Maximum sandbox/session lifetime and watchdog.
- Storage and egress caps.
- Resource isolation between workspaces.
- Dependency pinning and vulnerability scanning.
- Structured logs with PII and secrets redacted.
