# Tooling and infrastructure research

**Research date:** 2026-11-19

## Ingestion and storage
- Next.js App Router + TypeScript: browser studio.
- Uppy + @uppy/aws-s3: client-to-storage multipart uploads; its AWS S3 plugin supports S3-compatible services including Cloudflare R2 and server-generated signing endpoints.
- Cloudflare R2: private original media, proxies, thumbnails, final renders. R2 recommends multipart for large/resumable/parallel uploads; 5 MiB–5 GiB parts and up to 10,000 parts.
- Supabase Auth + Postgres: authentication, workspaces, creator/campaign metadata and job state. Do not store video bytes in Postgres.
- FastAPI: source validation and upload orchestration.
- Modal: short-lived CPU/GPU functions and asynchronous job dispatch.

Official references:
- Uppy S3 uploads: https://uppy.io/docs/aws-s3/
- Cloudflare R2 upload methods: https://developers.cloudflare.com/r2/objects/upload-objects/
- Cloudflare R2 pricing: https://developers.cloudflare.com/r2/pricing/
- Supabase signing keys/JWKS: https://supabase.com/docs/guides/auth/signing-keys
- Supabase MCP: https://supabase.com/docs/guides/ai-tools/mcp
- Modal Functions: https://modal.com/docs/sdk/py/latest/Function
- Modal FunctionCall: https://modal.com/docs/sdk/py/latest/FunctionCall

## Media quality tools
- FFmpeg/ffprobe: authoritative media probing, transcode, crop, composition, audio mixing, waveform and final encoding.
- PySceneDetect: detects cuts/fades and generates scene ranges. Treat as a signal, not an automatic highlight decision.
- faster-whisper: baseline ASR and word timestamps.
- WhisperX: optional forced alignment and diarization. Check exact model licenses; diarization quality is imperfect and overlapping speech can be difficult.
- Silero VAD: speech/non-speech segmentation; an additional signal for audio event analysis.
- OpenCV: low-rate frame sampling and facecam/gameplay layout analysis.
- pydub/librosa: optional audio feature extraction; benchmark performance against FFmpeg filters before adding.

## Video understanding model candidates
- TwelveLabs video understanding: benchmark for timestamped semantic search and contextual video Q&A.
- Google Gemini multimodal API: benchmark as an alternative for sampled-video understanding and editorial reasoning.

Do not select either provider from marketing claims alone. Benchmark both against the same manually annotated sample clips, measuring timestamp error, missed/false highlights, context accuracy, and cost per processed minute. Never allow a model response to execute a timeline or shell command directly. It should return constrained JSON validated against Clipro's timeline schema.

## Rendering
FFmpeg remains the baseline renderer and source of truth is the versioned timeline JSON. Remotion is a strong candidate for complex React compositions, but verify its commercial/automation license eligibility before using it in the automated production path.

## MCPs for internal development
- GitHub connector: available in this workspace for repository inspection, commits and PRs.
- Cloudflare MCP: official remote API and docs MCP servers can help inspect account resources, R2 bucket configuration and CORS. Use least privilege.
- Supabase MCP: project-scope it and start in read-only mode; never expose developer MCP to Clipro end users. Keep manual approvals on for writes.
- MakeMyClip Editor MCP: optional local editing workbench for prototyping timeline cuts/captions/FFmpeg operations; it is not our cloud processing backend.

References:
- Cloudflare MCP: https://github.com/cloudflare/mcp
- Supabase MCP: https://supabase.com/docs/guides/ai-tools/mcp
- MakeMyClip Editor: https://github.com/MakeMyClip/editor

No verified official Modal MCP server was found. Use the Modal Python SDK instead of adding an unreviewed community MCP to production.

## Cost and resource policy
- Start with CPU probing, scene detection and proxies.
- Use a GPU only for selected ASR/visual tasks after benchmarking.
- Process long VODs as bounded time chunks; do not load entire recordings into RAM.
- Persist media in R2; keep the relational database as metadata/job ledger.
- Enforce upload, storage, egress and compute quotas before exposing the service publicly.
- Do not add always-on monitoring to the manual-capture MVP.
