# Clipro architecture

## Product scope

Clipro is a private, single-operator AI clipping and video-editing workspace. There is one operator and no public registration, multi-user workspaces, invitations, roles, billing or public creator-facing accounts. ChatGPT in this conversation is the editorial brain; Clipro supplies media-processing and rendering tools. The initial workflow does not use a separate generative-model API or the user's ChatGPT subscription as an API credential. The operator explicitly hands analysis artifacts into this conversation and brings the resulting edit-plan JSON back into Clipro.

The first campaign is DiegoLoveless's Twitch GTA campaign. The system must still support other creator profiles, campaigns, platforms and generic uploaded videos without changing the editing engine.

## Core principles

- One private operator; no public SaaS account model.
- Hosted UI/API protected by an allowlisted private access layer (Cloudflare Access or equivalent).
- Platform-native capture and editing are separate.
- Public stream URLs/chat access are not raw media downloads.
- Use official viewer capture tools or creator-authorized media files.
- Never bypass access controls or use undocumented playback extraction.
- A source file must be explicitly supplied before processing.
- Clipro never publishes; finished videos are downloaded and posted manually.
- Creator, campaign and style profiles are data, not hard-coded editor logic.
- Live clips, VOD excerpts and ordinary uploaded videos use the same editor/render pipeline.

## System boundaries

### Private browser app

- No sign-up, invite, team or user-management screens.
- One default private library and one operator-owned project history.
- Choose/create streamer, campaign and style profiles.
- Choose platform (Twitch/Kick/YouTube) and source type.
- Display supported manual capture/download instructions.
- Upload source files with resumable multipart transfer.
- Show source metadata, processing status and downloadable analysis pack (timestamped transcript, audio cues, candidate ranges and visual contact sheets).
- Import a ChatGPT-generated, schema-validated edit-plan JSON.
- Show a rendered preview and QA report; support operator-directed revisions.
- Preview, approve/reject/regenerate and download final MP4, captions and timeline JSON.
- Later: multi-track manual editing and post-publish metrics entered by the operator.
- No social publishing integration.

### Private access layer

The browser application and API must be inaccessible to anonymous internet users. Prefer Cloudflare Access with an allowlist containing only the operator's identity. Protect both the web app and API hostname. The API must verify the access-layer identity assertion (for example, Cloudflare Access JWT) or use an equivalent server-side authentication mechanism; CORS alone is not authentication. Do not simply remove API authentication or expose a shared secret in browser JavaScript.

### Control plane

FastAPI owns source validation, media metadata, uploads, job lifecycle, editorial-plan state, rendering status, approvals and download authorization. Use a single-operator data model: no workspace membership joins or user IDs are needed for ordinary asset ownership. Keep a server-generated private project/library identifier if useful for grouping assets.

### Data plane

Modal workers own media probing, proxy generation, speech transcription, VAD/audio feature extraction, visual sampling, contact-sheet and analysis-pack generation, and deterministic rendering. ChatGPT in this conversation performs the editorial reasoning from the analysis pack and returns an edit-plan JSON for the operator to import. Do not call a separate LLM API in the initial release. Workers receive exact server-selected object keys and job IDs; never fetch arbitrary user-provided URLs.

For long VOD files, use chunked analysis and low-resolution proxy sampling. Never load an entire multi-hour source into RAM.

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
4. `creator_relay`: future optional creator-owned RTMPS/SRT feed.
5. `unsupported`: no source file or permitted acquisition route.

The renderer accepts files/assets, not arbitrary platform URLs. Arbitrary URL fetching is disabled.

## Platform source handling

### Twitch
Use permitted viewer-native clips created and downloaded manually when channel settings allow. Do not assume Editor permissions or invoke Editor-only APIs for the current campaign.

### Kick
Use permitted viewer-native clips created and downloaded manually when available. Do not assume channel-owner VOD download privileges.

### YouTube
A YouTube Clip URL is a reference, not a general MP4 download endpoint. Custom editing requires an authorized video file.

## ChatGPT-directed editorial and rendering pipeline

1. Probe the supplied source, validate codecs/duration and create safe low-resolution proxies.
2. Generate word-timestamped speech transcription, audio/VAD cues, scene-change information and sampled visual frames.
3. For long videos, scan in bounded chunks and generate ranked technical candidates; for short native clips, analyze the full clip.
4. Package the transcript, candidate timestamps, relevant frame contact sheets and campaign/style brief into an analysis pack that can be attached to this ChatGPT conversation.
5. ChatGPT reviews the supplied evidence, applies campaign/style rules, selects the strongest moment(s), explains the editorial rationale and returns a structured edit-plan JSON. This is a human-in-the-loop chat handoff, not an API call from Clipro to ChatGPT.
6. The operator imports the edit-plan JSON into Clipro. The app validates it against the timeline schema and effect allowlist.
7. The deterministic render workers apply cuts, captions, overlays, motion graphics, reframing, audio mixing and any configured licensed assets.
8. Automated technical/caption/audio checks create a QA report and preview.
9. The operator shares the preview/report in this conversation for ChatGPT editorial review, then requests changes or downloads the final result.

Never invent quotes, fake reactions or alter chronology to misrepresent events. For Diego, never make the creator look bad; prioritize GTA speedrun highlights, funny moments and genuine reactions.

## Campaign profiles

Campaign profiles are configurable data and can define creator/channel, allowed platforms and source types, date windows, game/topic, must-show rules, CTA, caption language, hashtags, editing style, duration/aspect ratio, retention targets, reference assets and duplicate/reuse limits.

Diego's GTA campaign is the first preset, not a global hard-coded rule. Other campaigns must not inherit Diego-specific restrictions.

## Timeline and rendering

Use the versioned schema in `packages/timeline/schema.json`. Remotion creates reusable compositions (animated captions, overlays, motion graphics, transitions, layouts and end cards); FFmpeg handles probing, trimming, composition inputs, audio mixing and final encoding. Verify Remotion license eligibility for the intended private/commercial use before production deployment.

The same renderer serves stream clips, uploaded VOD excerpts and ordinary manual video projects.

## Storage and security

- Store media in private object storage; keep only metadata and object keys in Postgres.
- Use short-lived upload/download URLs and server-generated object keys.
- Protect web app and API with a real private access layer; CORS is not access control.
- Verify the access-layer identity server-side on every API route.
- Never expose database, R2 or Modal credentials in the browser.
- Treat transcripts, chat, titles and comments as untrusted data.
- Validate ChatGPT-produced edit plans against JSON Schema and an effect allowlist before rendering.
- Never interpolate untrusted text into shell commands.
- Do not request platform passwords, stream keys or credentials.
- Require explicit operator review; publishing functionality is absent.
- Apply configurable retention and cleanup for source, proxy and rejected output files.

## Cost strategy

- Start with short native clips; add full VOD chunking after the short-clip pipeline is reliable.
- Use low-resolution proxy analysis and sparse visual sampling before expensive high-quality rendering.
- Use CPU for probe/segmentation/simple transforms; GPU only where it materially improves quality or throughput.
- Use speech transcription and media-analysis tools for evidence generation; ChatGPT performs editorial reasoning through the conversation. No separate generative AI API key is required for the initial workflow.
- Optional API-based automation can be considered later only if the operator explicitly wants unattended editorial decisions.
- No always-on stream monitoring in the manual-capture workflow.
