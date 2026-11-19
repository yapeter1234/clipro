# Modal deployment

This folder will contain the Modal app definitions. Keep long-running ingest separate from short-lived analysis/render functions.

## Planned Modal resources

- `clipro-api`: web endpoint for the FastAPI control plane.
- `clipro-ingest`: supervised live ingest process/MediaMTX, using authenticated ingress.
- `clipro-analyze`: CPU-first window analysis.
- `clipro-asr`: faster-whisper transcription worker.
- `clipro-vision`: optional GPU worker invoked only for ranked candidates.
- `clipro-tts`: Kokoro narration worker.
- `clipro-render`: Remotion/FFmpeg rendering worker.
- `clipro-cleanup`: TTL and temporary media cleanup.

## Required secrets (names only)

Do not commit secret values:
- `CLIPRO_APP_SECRET`
- `TWITCH_CLIENT_ID`
- `TWITCH_CLIENT_SECRET`
- `KICK_CLIENT_ID`
- `KICK_CLIENT_SECRET`
- `YOUTUBE_API_KEY` (if used)
- `DATABASE_URL` (if using managed Postgres)
- `OBJECT_STORAGE_* ` (only if configured)

Only create platform secrets after the corresponding adapter is implemented and the user authorizes that platform.

## Deployment gates

1. Prove RTMPS ingress works from a creator-owned test encoder.
2. Prove a bounded buffer can recover after a worker restart.
3. Verify TLS and per-session ingest-key revocation.
4. Verify Modal egress, GPU and Sandbox costs on a short test.
5. Verify cleanup removes expired source material.
6. Add observability and hard spending quotas before a long monitoring session.

Modal Sandbox lifetime is bounded. Never rely on one process running indefinitely; checkpoint monitor state, use a watchdog and restart gracefully.
