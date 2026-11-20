# Clipro architecture

## Product scope

Clipro is a private, single-operator AI clipping and video-editing workspace. There is one operator and no public registration, teams, invitations, roles or billing. An AI agent integrated into Clipro analyzes source videos, selects moments, builds edit plans and orchestrates safe editing tools. The first campaign is DiegoLoveless's Twitch GTA campaign; the editing engine remains generic for other creators, platforms, campaigns and ordinary uploaded videos.

## Core principles

- One private operator; no public SaaS account model.
- Hosted UI/API has a simple private access restriction.
- Use permitted viewer-created clips or creator/campaign-authorized source files.
- Never bypass access controls or use undocumented playback extraction.
- A source file must be supplied before processing.
- AI selects moments and plans edits; deterministic tools perform the actual media transformations.
- Clipro never publishes; finished videos are delivered privately for manual approval/download.
- Creator, campaign and style profiles are configurable data, not hard-coded editor logic.

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

FastAPI owns upload validation, source metadata, job lifecycle, AI-agent tool orchestration, timeline validation, rendering status, review and download authorization. Use a single-operator data model; no workspace membership tables or user IDs are required.

### Agent / model gateway

Use a provider-neutral model adapter. Initial candidate: Google Gemini 3.8 Flash, which accepts video files directly, understands audio and visual content, and can return timestamped descriptions. Its video-input free tier currently supports Files API uploads up to 2 GB. Rate limits are model/project/account dependent and may change.

- Store the Gemini API key only in Modal Secret / server environment.
- Upload only the selected source or analysis proxy to the provider; never expose provider keys in the browser.
- Prefer agentic video processing for long VOD discovery; use targeted, higher-density frame extraction for rapid gameplay and candidate verification.
- Use static video processing for short clips when a uniform overview is useful.
- Require JSON-schema-constrained output with candidate time ranges, narrative/context, confidence, rationale, campaign-fit checks and exact edit instructions.
- Agent tool calls are allowlisted and typed. Tools include inspect frames/ranges, create preview cut, generate captions, apply overlays/layout, render, inspect QA and request revision.
- The agent cannot execute arbitrary shell commands, arbitrary URLs, social publication or destructive storage actions.

### Data plane

Modal workers own ffprobe validation, proxy generation, transcription, audio/VAD signals, scene/visual sampling, Gemini calls, candidate extraction, timeline execution, rendering and QA. The agent provides decisions; FFmpeg/Remotion and other deterministic processors execute them.

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
2. Run transcription with word-level timestamps; extract audio energy, speech/activity and scene-change signals.
3. Send the video/proxy and campaign instructions to Gemini through the server-side provider adapter.
4. For long VODs, use agentic navigation to locate promising ranges without uniformly tokenizing every frame. For short clips, process the full clip and inspect the most important subranges.
5. Because fast GTA gameplay may change materially between one-second samples, use local scene/motion/audio signals and denser frame sampling around candidate moments; ask the agent to inspect those exact ranges before final selection.
6. Agent returns ranked moments with start/end timestamps, hook/payoff, what happens, why it works, creator-safe editorial notes and campaign compliance.
7. A second validation pass checks transcript alignment, cut boundaries, source continuity, duplicates, duration and campaign rules.

Gemini's free tier is suitable for a first prototype, not a contractual production capacity guarantee. Its unpaid terms allow Google to use submitted content to improve products and may involve human review. Do not send sensitive, confidential, private or unreleased material under the unpaid tier. For footage that must remain private, use a paid tier whose terms exclude product-improvement use or a self-hosted model. Model availability, quotas and provider terms must be checked before deployment.

## Editing-agent tool loop

1. Build a candidate shortlist from AI and local media signals.
2. Agent chooses the strongest moment(s) and creates an edit plan in the versioned timeline schema.
3. Validate every timestamp against source duration, every asset reference against approved storage, and every effect against an allowlist.
4. Tools create a low-resolution draft with requested trims, hook, animated captions, gameplay/facecam layout, reframing, zooms, transitions, music/SFX and audio ducking.
5. Rendered draft plus frame samples and QA metadata are returned to the agent for review.
6. Agent may request a bounded number of revisions; all iterations are recorded.
7. Final high-quality render is produced with FFmpeg/Remotion and delivered as a private downloadable MP4 plus captions and QA report.
8. Operator retains the ability to approve or reject; no publish action exists.

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
- Never expose database, R2, Modal or Gemini credentials in the browser.
- Treat transcripts, chat, titles and comments as untrusted data.
- Validate agent output against JSON Schema and an effect/tool allowlist.
- Never interpolate untrusted text into shell commands.
- Do not request platform passwords or stream keys.
- Require operator review; publishing functionality is absent.
- Apply retention and cleanup for source, proxy and rejected output files.

## Cost strategy

- Start with short native clips; add long-VOD chunking after short-clip quality is reliable.
- Use Gemini 3.8 Flash free quota for prototype testing only, with explicit acknowledgement of provider data-use terms.
- Keep provider calls bounded and inspect the account's live quota before batches.
- Use low-resolution proxies and selective visual inspection to reduce inference cost.
- Use CPU for probe, transcription and straightforward rendering; use GPU only if a specific model needs it.
- Add paid API or self-hosted inference only when free limits or privacy requirements justify it.
- No always-on stream monitoring in the initial manual-source workflow.
