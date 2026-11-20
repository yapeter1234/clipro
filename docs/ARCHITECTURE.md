# Clipro architecture

## Product scope

Clipro is a private, single-operator AI clipping and video-editing workspace. It has no public registration, teams, invitations, roles or billing. A self-hosted multimodal AI agent analyzes source videos, selects moments, builds edit plans and orchestrates editing tools. The first campaign is DiegoLoveless's Twitch GTA campaign; the editing engine remains generic for other creators, platforms, campaigns and ordinary uploaded videos.

## Core principles

- One private operator; no public SaaS account model.
- Hosted UI/API has a simple private access restriction.
- Use permitted viewer-created clips or creator/campaign-authorized source files.
- Never bypass access controls or use undocumented playback extraction.
- A source file must be supplied before processing.
- The model selects moments and plans edits; deterministic tools perform media transformations.
- Host open-weight model inference on Modal rather than relying on an external generative-model API.
- Clipro never publishes; finished videos are delivered privately for manual approval/download.

## System boundaries

### Private browser app

- No sign-up, teams or user-management screens.
- One private project/library history.
- Upload permitted source media; choose creator/campaign/style presets.
- Show analysis progress, candidate highlights, edit plan and quality report.
- Preview candidate segments and finished render.
- Allow operator to accept, reject or request revisions.
- Download final MP4 and project/timeline data.
- No social publishing integration.

### Control plane

FastAPI owns upload validation, source metadata, job lifecycle, agent-tool orchestration, timeline validation, rendering status, review and download authorization. Use a single-operator data model; no workspace membership tables or user IDs are required.

### Modal GPU model host and agent runtime

Run the selected open-weight multimodal model on Modal GPUs with a compatible engine such as vLLM or SGLang. Initial candidate: Qwen3.6-35B-A3B. Verify exact model revision, video support, engine compatibility, GPU memory requirements and license before pinning deployment.

Modal can serve custom/open models and scale GPU workloads down when idle. Use serverless functions/containers for model inference and processing jobs, with a volume or cache for model weights when appropriate. Avoid leaving an expensive GPU worker hot when the private tool is idle.

Keep the model behind a provider-neutral inference adapter. Do not integrate Modal's separately token-billed Model APIs for the initial self-hosted path. The Starter plan's monthly compute credit can offset GPU/CPU compute, but does not make GPU inference unlimited or guarantee all workloads fit within the credit. Set a workspace budget and report estimated job cost.

The model agent receives:
- the private source video or bounded clips/proxies;
- transcript with word timestamps;
- sampled frames and scene/motion/audio cues;
- creator, campaign and style instructions;
- current candidate list and edit/render feedback.

The agent may call only explicit typed tools, such as inspect a timestamp range, retrieve a frame/contact sheet, create a preview cut, generate captions, apply an allowlisted overlay/layout, render a draft, inspect QA and request a bounded revision. Never allow arbitrary shell commands, arbitrary URLs, or publishing actions.

### Data plane

Modal workers own ffprobe validation, proxy generation, speech transcription, audio/VAD signals, scene/visual sampling, model inference, candidate extraction, timeline execution, rendering and QA. The agent makes editorial decisions; FFmpeg/Remotion and other deterministic processors execute them.

## Source abstraction

A source record should include:
- source/asset ID;
- platform and creator/channel;
- source kind: live_stream, past_broadcast or uploaded_video;
- acquisition mode;
- source URL/clip URL as reference only;
- private file asset ID (required to edit);
- duration, dimensions, frame rate and audio streams;
- optional campaign/style profile IDs;
- authorization basis/notes;
- checksum and retention policy.

Acquisition modes:
1. `viewer_native_clip_manual_download`: operator creates and downloads a native Twitch or Kick clip and uploads it.
2. `authorized_source_file`: creator/campaign supplies a video or excerpt.
3. `youtube_clip_reference`: stores a YouTube Clip URL only; no raw media processing until an authorized source file is uploaded.
4. `unsupported`: no source file or permitted acquisition route.

The renderer accepts files/assets, not arbitrary platform URLs. Arbitrary URL fetching is disabled.

## Video understanding and highlight selection

1. Validate the file with ffprobe and create a low-resolution proxy where appropriate.
2. Transcribe speech with word-level timestamps; extract audio energy, speech/activity, scene-change and motion signals.
3. Split long sources into bounded segments. Extract timestamped frames/contact sheets and retain exact source-time offsets.
4. Send supported video segments and frame sequences with timestamps, transcript and campaign instructions to the Modal-hosted multimodal model.
5. Use broad temporal sampling for discovery, then denser frame/audio inspection around candidate moments. A one-frame-per-second pass alone is insufficient for fast GTA gameplay.
6. Model returns ranked moments with exact start/end timestamps, context, hook/payoff, what happens, why it works, creator-safe notes and campaign compliance.
7. The agent uses inspection tools to verify candidate boundaries and surrounding context.
8. Validate transcript alignment, source continuity, duplicate moments, duration and campaign requirements before rendering.

The initial model candidate is Qwen3.6-35B-A3B. Its published model information lists text, image and video inputs and tool-calling capabilities; verify the deployed serving engine's actual video input path before treating it as production-ready. If direct video ingestion is not supported by the chosen engine version, pass sampled frames and timestamps instead.

## Editing-agent tool loop

1. Build candidate ranges from model understanding and local media signals.
2. Agent chooses the strongest moment(s) and emits a structured edit plan in the versioned timeline schema.
3. Validate every timestamp against source duration, every asset reference against approved storage, and every effect against an allowlist.
4. Editing tools create a low-resolution draft with trims, hook, animated captions, gameplay/facecam layout, reframing, zooms, transitions, music/SFX and audio ducking.
5. Return draft preview, sampled frames and QA metadata to the agent.
6. Agent may request a bounded number of corrections; every iteration is recorded.
7. Final high-quality render is produced with FFmpeg/Remotion and delivered as a private downloadable MP4 plus captions and QA report.
8. Operator can approve, reject or request another revision; there is no publish tool.

Never invent quotes, fake reactions or alter chronology to misrepresent events. For Diego, never make the creator look bad; prioritize GTA speedrun highlights, funny moments and genuine reactions.

## Campaign profiles

Campaign profiles define creator/channel, allowed platforms and source types, date windows, game/topic, must-show rules, CTA, caption language, hashtags, editing style, duration/aspect ratio, retention targets, reference assets and duplicate/reuse limits.

Diego's GTA campaign is the first preset, not a global hard-coded rule. Other campaigns must not inherit Diego-specific restrictions.

## Timeline and rendering

Use the versioned schema in `packages/timeline/schema.json`. Remotion creates reusable compositions (animated captions, overlays, motion graphics, transitions, layouts and end cards); FFmpeg handles probing, trimming, composition inputs, audio mixing and final encoding. Verify Remotion license eligibility for the intended use before production deployment.

The same renderer serves stream clips, uploaded VOD excerpts and ordinary manual video projects.

## Storage and security

- Store media in private object storage; keep only metadata and object keys in the metadata store.
- Use short-lived upload/download URLs and server-generated object keys.
- Protect dashboard and API even though there is one operator; do not rely on obscurity alone.
- Never expose database, R2, Modal or model credentials in the browser.
- Treat transcripts, chat, titles and comments as untrusted data.
- Validate agent output against JSON Schema and an effect/tool allowlist.
- Never interpolate untrusted text into shell commands.
- Do not request platform passwords or stream keys.
- Require operator review; publishing functionality is absent.
- Apply retention and cleanup for source, proxy and rejected output files.

## Cost and privacy strategy

- Modal's Starter tier currently includes a limited monthly compute credit; it offsets GPU/CPU time but does not guarantee free unlimited inference.
- Self-hosted open-weight inference uses compute billing, not token billing. Modal-hosted Model APIs are a separate token-billed product and are not part of this design.
- Start with one short clip and a smaller/quantized configuration for compatibility testing; benchmark quality and throughput before scaling model size.
- Autoscale GPU workers to zero when idle; avoid always-on GPU allocations.
- Bound video segments, sampled frames, agent tool calls and revision count.
- Check the model weights' license and third-party rendering/music/voice licenses before deployment.
- No always-on stream monitoring in the initial manual-source workflow.
