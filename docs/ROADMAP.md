# Roadmap and acceptance criteria

## M0 — source and timeline contracts
- [x] Repository scaffold, timeline schema and campaign/style architecture.
- [x] Define manual source acquisition boundaries for Twitch/Kick/YouTube.
- [x] Add source-policy tests and ffprobe helper tests.
- [ ] Verify private upload/storage/Modal integration against real accounts.

**Exit:** permitted source files can be safely ingested independent of creator/campaign.

## M1 — private single-operator foundation
- [x] Browser upload dashboard and Uppy multipart upload foundation.
- [x] R2 multipart orchestration and server-side object verification.
- [x] Modal media-probe worker and durable job records.
- [ ] Remove Supabase Auth, magic-link sign-in, user IDs, workspaces and membership joins.
- [ ] Defer Supabase/Postgres initially; use the simplest reliable job/asset metadata store.
- [ ] Add one simple private access restriction for the hosted dashboard and API.
- [ ] Keep R2 private with short-lived upload/download URLs.
- [ ] Configure and verify R2 and Modal.
- [ ] Add asset preview/download and retention cleanup.

**Exit:** operator uploads a permitted video; its metadata, thumbnail and private asset state are validated and visible.

## M2 — Modal-hosted video agent
- [ ] Deploy a provider-neutral model adapter on Modal GPUs.
- [ ] Test Qwen3.6-35B-A3B with a compatible vLLM/SGLang serving version; verify model license, video input and tool-calling paths.
- [ ] Benchmark a smaller/quantized fallback against the larger candidate using real gameplay clips.
- [ ] Add timestamped transcript, VAD/audio cues, scene-change and motion signals.
- [ ] Add bounded long-video segmentation and high-density candidate frame extraction.
- [ ] Implement the agent tool loop: inspect ranges, compare context, rank moments and emit validated edit-plan JSON.
- [ ] Add quota/compute-budget-aware retries, concurrency limits and scale-to-zero GPU operation.
- [ ] Keep inference private to Modal; do not require a Google/OpenAI model API key.

**Exit:** after an upload, the Modal-hosted agent actually inspects source video evidence, finds the best moments, explains selection and emits an executable edit plan.

## M3 — professional editing and rendering
- [ ] Execute validated agent edit plans using FFmpeg and Remotion.
- [ ] Context-aware hooks and title treatments without misrepresenting events.
- [ ] Accurate animated word-synchronized captions.
- [ ] Purposeful transitions, zooms, punch-ins and motion graphics.
- [ ] Smart gameplay/facecam layouts and reframing.
- [ ] Optional original narration using an appropriately licensed local/hosted voice model.
- [ ] Licensed music/SFX library and rights metadata.
- [ ] Voice/music ducking, normalization and final audio QA.
- [ ] Render high-quality MP4 and technical/editorial report.
- [ ] Feed draft preview/QA evidence back to the agent for bounded revision.

**Exit:** a polished MP4 is automatically created from an agent-selected moment and passes automated QA.

## M4 — private delivery and review
- [ ] Preview finished render in private dashboard.
- [ ] Agent-generated review summary and quality report.
- [ ] Operator can request revisions, approve or reject.
- [ ] Download MP4, captions and timeline JSON.
- [ ] Preserve project/edit revisions.
- [ ] Enforce publication disabled server-side.

**Exit:** final videos are privately delivered to the operator; nothing is published automatically.

## M5 — additional sources and generic editing
- [ ] Twitch/Kick viewer-native capture guidance.
- [ ] YouTube Clip reference and authorized-file workflow.
- [ ] Generic uploaded-video intake independent of streaming platform.
- [ ] Source-range selection and chunked processing for long video.
- [ ] Multi-track manual editing, caption/overlay editing and export revisions.

**Exit:** the same private tool handles stream-derived clips and ordinary uploaded videos.

## Not in scope
- Public sign-up, multiple users, teams, invitations, roles or billing.
- Automatic publishing to social platforms.
- Downloading arbitrary public stream URLs or bypassing platform restrictions.
- Twitch Editor role for Diego unless separately authorized.
- Unofficial playback extraction.
- Always-on livestream monitoring in initial manual-source workflow.
- Engagement/audience guarantees.
