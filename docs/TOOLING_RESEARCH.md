# Tooling and infrastructure research

**Research date:** 2026-11-19

## Recommended baseline

| Concern | Recommendation | Status |
|---|---|---|
| Browser dashboard | Next.js App Router + TypeScript | Selected |
| Large browser uploads | Uppy Dashboard + @uppy/aws-s3 with server-side request signing | Selected |
| Authentication and metadata | Supabase Auth + Postgres with workspace-scoped RLS | Recommended; project not connected |
| Original media and rendered files | Private Cloudflare R2 bucket, S3 API | Recommended; bucket not provisioned |
| API/control plane | FastAPI | Python API area exists; entrypoint added in M1a |
| Compute and jobs | Modal serverless Functions; Function.spawn() for asynchronous work | Selected; not deployed |
| Media inspection | FFmpeg/ffprobe | Selected |
| Scene-change signals | PySceneDetect | Candidate |
| Speech transcription | faster-whisper first; WhisperX only where alignment/diarization is needed | Candidate |
| Voice activity | Silero VAD | Candidate |
| Timeline rendering | FFmpeg baseline; Remotion for React-driven compositions after license confirmation | Conditional |
| Voiceover | Kokoro candidate; validate exact model/runtime license and voice rights before bundling | Not selected |

## Upload and storage

### Uppy + Cloudflare R2

Use Uppy with its AWS S3 plugin and the S3-compatible Cloudflare R2 endpoint. Configure server-side signing and multipart callbacks so R2 credentials never reach the browser. Use multipart for large media so failed parts can be retried without restarting the upload. Do not proxy multi-gigabyte video through FastAPI.

Official references:
- Uppy S3 uploads and multipart signing: https://uppy.io/docs/aws-s3/
- Uppy Next.js integration: https://uppy.io/docs/nextjs/
- Cloudflare R2 upload methods: https://developers.cloudflare.com/r2/objects/upload-objects/
- Cloudflare R2 pricing: https://developers.cloudflare.com/r2/pricing/

Cloudflare's published R2 Standard free tier currently includes 10 GB-month storage, 1 million Class A operations and 10 million Class B operations monthly. Internet egress is listed as free. Above the free tier, Standard storage is listed at $0.015/GB-month. These are current published rates, not a guaranteed future quote.

### Supabase: metadata and authentication, not media blobs

Supabase Free currently includes a 500 MB database, 1 GB file storage and 50,000 monthly active users; free projects pause after one week of inactivity. That is suitable for prototype metadata and sign-in, but not a place to keep large source videos and exports. Use Supabase Auth + Postgres/RLS while putting media in R2.

References:
- Pricing: https://supabase.com/pricing
- Next.js App Router auth: https://supabase.com/docs/guides/auth/quickstarts/nextjs
- SSR sessions: https://supabase.com/docs/guides/auth/server-side

### Storage layout

Keep buckets private. Use immutable, generated object keys instead of user-provided paths:

- workspaces/{workspace_id}/sources/{asset_id}/original.{ext}
- workspaces/{workspace_id}/assets/{asset_id}/proxy.mp4
- workspaces/{workspace_id}/renders/{render_id}/final.mp4
- workspaces/{workspace_id}/renders/{render_id}/timeline.json

Persist object keys, checksums, size, MIME type, rights metadata and retention timestamps in Postgres. Store no video binary in Postgres. Generate short-lived signed URLs only when the UI or a worker needs access.

## Modal compute strategy

Modal is a good fit for bursty work because Functions scale on demand and are billed by active compute time. The current Starter plan lists $30/month of included compute credit; Model APIs and external services can still incur separate charges. Modal lists 1 TiB/month of included Volume storage, subject to current terms.

Use separate stages with bounded concurrency:

1. Probe/validate (CPU): ffprobe, streams, duration, codec, dimensions, frame rate, audio presence and basic integrity.
2. Proxy/thumbnails (CPU): low-resolution proxy, contact sheet and waveform.
3. Candidate analysis (CPU first): audio energy, VAD, scene changes and transcript signals.
4. ASR/visual reasoning (GPU only when benchmarked as necessary): process selected windows, not every frame of a multi-hour VOD.
5. Render (CPU first): deterministic FFmpeg composition; use GPU only when a selected effect/model requires it.

Use Function.spawn() to start long-running work without blocking an HTTP request and persist the Modal FunctionCall ID alongside the Clipro job ID. The database remains the durable job ledger. A Modal Volume needs explicit reload/commit behavior; R2 remains the durable source-media store.

References:
- Modal pricing: https://modal.com/pricing
- Modal Functions: https://modal.com/docs/sdk/py/latest/Function
- Modal FunctionCall: https://modal.com/docs/sdk/py/latest/FunctionCall
- Modal CloudBucketMount (including Cloudflare R2): https://modal.com/docs/sdk/py/latest/CloudBucketMount
- Modal Volumes: https://modal.com/docs/sdk/py/latest/Volume

## Analysis components

### FFmpeg / ffprobe

Use ffprobe for authoritative media metadata and FFmpeg for deterministic transforms, proxies, thumbnails, waveform extraction, audio mixing and final encoding. Invoke subprocesses with argument arrays, never with shell strings assembled from model output. Browser MIME type and extension are only preliminary checks; inspect actual media after upload.

### PySceneDetect

PySceneDetect detects cuts/fades and returns scene time ranges. This is one signal for candidate windows, not a highlight detector by itself.

Reference: https://www.scenedetect.com/docs/latest/

### faster-whisper and WhisperX

Start with faster-whisper for transcription and word timestamps. Add WhisperX only if tests show we need its alignment or diarization behavior. WhisperX is BSD-2-Clause, but it can pull in separate models and dependencies; pyannote components have their own licenses and model-access conditions. Record the exact model and dependency license per deployed image.

Reference: https://github.com/m-bain/whisperX

### VAD, visual signals and editorial reasoning

Combine VAD/audio energy, transcript structure, scene-change signals and sampled frames. Do not let one signal automatically decide a highlight. The editorial planner should explain why a range is promising, preserve chronology and reject false context. Campaign compliance, rights and creator-protection gates remain deterministic code outside the model.

## Rendering and licensing gate

FFmpeg is the baseline because it is deterministic and scriptable. The Clipro timeline JSON remains the source of truth for automatic edits and the future manual editor.

Remotion is a strong candidate for animated captions, reusable React compositions and motion graphics. Its published pricing currently distinguishes a free license for individuals and companies of up to three people from a separate automation offering listed at $0.01 per render with a $100/month minimum. Before using it in a commercial automated editor, confirm eligibility under the actual license terms. Do not assume the pricing table overrides the license.

Reference: https://www.remotion.dev/docs/license/pricing

If the applicable Remotion license is not acceptable, keep the same timeline abstraction and render the first styles with FFmpeg filters/ASS subtitles, SVG overlays and pre-rendered motion assets.

## MCPs worth using

MCP is useful for development, inspection and repeatable operations. It should not sit in the production critical path for every clip.

| MCP / tool | Use in Clipro work | Cautions |
|---|---|---|
| GitHub connector | Already available in this workspace; inspect repository and commit changes | Review diffs and run CI before merging |
| Cloudflare API MCP | Inspect/manage R2 account, bucket settings and CORS | Connect via OAuth; grant only required permissions; review writes |
| Supabase MCP | Inspect schema, RLS and migrations | Scope to one project and read-only for exploration; never expose developer MCP to end users |
| MakeMyClip Editor MCP | Optional local workbench to prototype cuts, captions and FFmpeg operations | Local-only; not our cloud worker or production renderer; audit code and FFmpeg licensing |
| Other video-editing MCPs | Research/prototype only | Do not add unreviewed code/tool outputs to production |

Cloudflare provides a remote API MCP at https://mcp.cloudflare.com/mcp and a documentation MCP at https://docs.mcp.cloudflare.com/mcp. Its official server repository lists R2 among supported products.

Supabase provides a remote MCP at https://mcp.supabase.com/mcp. Its docs recommend project scoping and read-only mode where possible, and warn against exposing the developer MCP to customers.

MakeMyClip Editor (MIT) exposes local FFmpeg timeline operations over CLI, browser UI and MCP. It may help evaluate edit primitives quickly, but its README describes a local-only workflow; it does not solve Modal cloud execution, Clipro storage, multi-streamer state or contextual streamer editing. Do not make it a runtime dependency.

References:
- Cloudflare MCP: https://github.com/cloudflare/mcp
- Cloudflare MCP server overview: https://github.com/cloudflare/mcp-server-cloudflare
- Supabase MCP security guidance: https://supabase.com/docs/guides/ai-tools/mcp
- MakeMyClip Editor: https://github.com/MakeMyClip/editor

No dedicated official Modal MCP server was verified in this research. Use Modal's Python SDK and CLI rather than installing an unrelated community MCP for production deployment.

## Decisions not to take yet

- Do not deploy always-on live-stream monitoring for the current manual-capture workflow.
- Do not scrape or download arbitrary public stream/VOD URLs.
- Do not choose an LLM or visual model before benchmarking actual GTA gameplay/facecam samples.
- Do not bundle a voice, music or SFX asset until its use and redistribution rights are recorded.
- Do not turn on publishing APIs. Final approval and publication stay with the user.
- Do not make engagement rate, Tier 1 audience share or a 30-day online period pre-render guarantees; these are post-publication metrics to monitor.
