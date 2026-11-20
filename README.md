# Clipro

**Clipro is a public prototype for AI-assisted video clipping and editing.** Anyone with the prototype URL can upload an authorized video, run highlight discovery and review suggested moments. There are no user accounts, passwords, sessions, API signing secrets, teams or billing flows.

## Prototype workflow

1. A visitor uploads a permitted native clip or authorized video file.
2. Clipro stores the source in private R2 storage and records its metadata/job in Postgres.
3. Modal provisions short-lived workers for media probing and AI analysis.
4. The analysis worker transcribes audio locally, samples video frames and uses Qwen2.5-VL to identify candidate highlights.
5. The dashboard displays ranked timestamps for review.
6. MP4 rendering, captions, preview and download are the next implementation milestone.

## Hosting and infrastructure

| Layer | Technology |
|---|---|
| Public dashboard | Next.js on Vercel |
| Public API/control plane | FastAPI on Modal |
| Media storage | Cloudflare R2 |
| Metadata and processing jobs | Postgres (Supabase-hosted in current setup) |
| Media workers and GPU inference | Modal |
| Media processing | FFmpeg |
| Highlight model | Qwen2.5-VL-3B-Instruct |
| Transcription | faster-whisper small |

No Supabase Auth, Supabase client key, user password, browser session or shared Clipro API signing secret is used. Postgres remains necessary for the current implementation because upload sessions, asset metadata and processing jobs are stored there. R2 remains necessary because the browser uploads video chunks directly to object storage. Modal hosts the API and compute workers.

Infrastructure credentials (Postgres URL, R2 keys, Modal token) remain server-side in Modal Secrets. They are service-to-service credentials, not user authentication.

## Public prototype caveat

This is intentionally open. Anyone who can reach the URL can submit uploads and trigger processing, potentially consuming R2 storage and Modal GPU credits. There are no per-user quotas, private workspaces or abuse controls yet. Do not put sensitive or private footage in this prototype. The R2 bucket itself remains private; the application issues short-lived upload operations.

## Source acquisition rules

- Upload only video files you are authorized to edit.
- A public stream URL is not treated as a downloadable video file.
- No access-control bypass, undocumented playback extraction or unauthorized full-VOD downloading.
- Publishing is manual; nothing is posted automatically.

## Current status

Implemented in the feature branch: browser multipart upload, R2 storage integration, Postgres asset/job records, Modal media probe, Modal Qwen/Whisper highlight-analysis worker, and dashboard display of candidate timestamps.

Not yet end-to-end deployed or verified: Vercel, Postgres, R2 and Modal account configuration. Also not yet implemented: actual clip rendering/export, caption generation, preview and download.

See [ROADMAP.md](docs/ROADMAP.md), [ARCHITECTURE.md](docs/ARCHITECTURE.md), and [source acquisition guide](docs/INGESTION_NO_OBS.md).
