# Clipro architecture

## Product scope

Clipro is a multi-streamer, multi-platform AI clipping and short-form video editing studio. It is not hard-coded to Diego or to one campaign.

A job can start from:
- a native clip captured from a live stream;
- a native clip captured from a past broadcast/VOD;
- a creator/campaign-authorized uploaded video file;
- a future creator-authorized continuous media feed.

The first pilot is DiegoLoveless's Twitch GTA campaign, using viewer-created clips downloaded manually. The same editing engine, timeline schema and browser review flow serve all other creators and campaigns.

## Core principles

- Platform-native capture and editing are separate.
- Public stream URLs/chat access are not raw media downloads.
- Use official viewer capture tools or creator-authorized media files.
- Never bypass access controls or use undocumented playback extraction.
- A user must explicitly supply/authorize the source file before processing.
- Clipro never publishes in the MVP. Rendered clips are downloaded and posted by the user.
- Source profiles, campaign rules, and visual style profiles are independent and configurable.
- Live clips and archived-video clips use the same editor/render pipeline.

## System boundaries

### Browser app

- Create/select streamer profiles.
- Create/select campaign profiles.
- Choose platform (Twitch/Kick/YouTube).
- Choose source type (live stream/past broadcast/uploaded video).
- Display platform-specific clip/download instructions.
- Upload source files using a secure browser upload flow.
- Show upload progress, media metadata, clip range selector and analysis job status.
- Preview automatically edited results.
- Approve/reject/regenerate and download MP4, captions and timeline JSON.
- Later: multi-track manual editing.
- After user posts manually, record URL and analytics evidence.
- No publishing integration in the MVP.

### Control plane

FastAPI owns authentication, workspaces, streamer/campaign/style profiles, source metadata, uploads, job lifecycle, rendering status, approvals and post-publish metrics.

### Data plane

Modal workers own media probing, proxy generation, ASR/VAD, highlight detection, editorial planning, TTS, motion graphics and rendering.

For long VOD files, use a source-range selector and chunked analysis; never load the entire multi-hour video into RAM. For native clips, process the complete short file.

## Source abstraction

Define a source object with:
- source_id;
- platform;
- creator/channel;
- source_kind: live_stream, past_broadcast, uploaded_video;
- acquisition_mode;
- source_url/clip_url (reference only);
- file asset ID (required to edit);
- source duration, dimensions, frame rate and audio streams;
- campaign/style profile IDs;
- authorization evidence/notes;
- checksum and retention policy.

Acquisition modes:
1. `viewer_native_clip_manual_download`: user creates and downloads a native Twitch or Kick clip and uploads it.
2. `authorized_source_file`: creator/campaign supplies a video or excerpt.
3. `youtube_clip_reference`: stores a YouTube Clip URL only; no raw media processing until an authorized source file is uploaded.
4. `creator_relay`: future optional RTMPS/SRT creator-owned feed.
5. `editor_api`: optional future Twitch Editor integration for channels that explicitly grant it; disabled for Diego.
6. `unsupported`: no source file or permitted acquisition route.

The renderer accepts files/assets, not arbitrary platform URLs. Arbitrary URL fetching is disabled.

## Platform source handling

### Twitch
Logged-in viewers can create clips from live streams and VODs when channel clip settings permit and the viewer is not restricted. Clips are 5–60 seconds. A viewer can download clips they created from Clips Manager. Diego's job uses this manual workflow. Editor-only Create Clip From VOD/Get Clips Download endpoints are not invoked.

### Kick
Logged-in viewers can create clips from live streams and VODs when enabled. Clips are 10–180 seconds; viewers can download clips they created. Full VOD downloads are available to the channel owner only, so the app must not download another creator's VOD.

### YouTube
YouTube Clips are shareable 5–60-second excerpts, not an MP4 download endpoint for the Clipro renderer. Live clipping requires eligible DVR/broadcast conditions, and the clip may not be playable until the archive is processed. Custom editing requires an authorized video file from the creator/campaign.

### Future direct feeds
A creator may optionally provide an authorized second output into secure RTMPS/SRT ingress (MediaMTX). This is not required by the current user or Diego campaign.

## AI editing pipeline

1. Probe media, inspect source game/category metadata if present.
2. For full uploaded VODs, scan in chunks and extract candidate ranges using audio, transcript, chat if legitimately available, and low-rate visual signals.
3. For short native clips, analyze the complete clip.
4. Apply campaign gate: platform, game/topic, creator visibility, source type and prohibited content.
5. Analyze the narrative and create a structured edit plan.
6. Generate accurate captions, optional original narrator script/TTS, licensed music/SFX, hooks, CTA, transitions, motion and reframe.
7. Render with the reusable timeline engine.
8. Run technical and campaign QA.
9. Present the finished result for manual approval/download.

AI must never generate fake quotes or alter chronology to misrepresent what happened. For Diego, never make the creator look bad.

## Campaign profiles

Campaign profiles are data, not application constants. A profile can define:
- creator/channel and allowed source platform(s);
- source types and date windows;
- allowed game/franchise or topic;
- clip must-show rules;
- required CTA;
- caption language, hashtags and disclosures;
- content style and restrictions;
- output duration/aspect ratio;
- likes-visible, post lifespan and post-publish analytics targets;
- reference videos/assets;
- duplicate/reuse limits.

The Diego profile is one instance. Other Twitch/Kick/YouTube creators get their own profiles and cannot inherit Diego-specific rules.

## Timeline and rendering

Use the versioned schema in `packages/timeline/schema.json`. Remotion creates reusable compositions (animated captions, overlays, motion graphics, transitions, layouts and end cards); FFmpeg handles probing, trimming, composition inputs, audio mixing and final encoding.

The same timeline renderer serves native clips, uploaded VOD excerpts and future manually arranged video projects.

## Post-publish metrics (user-entered initially)

Clipro does not publish. It can track a manually entered post URL, date, likes-visible confirmation, 30-day minimum-live reminder, views, likes, comments, shares, engagement rate and Tier 1 audience share. Analytics can only be marked verified when the user supplies platform analytics evidence or a supported official analytics integration exists.

## Storage and security

- Media stored outside relational DB, referenced by asset ID/checksum.
- Uploads use short-lived signed URLs, file limits, type probing and workspace access checks.
- Delete/expire source and rejected output files by configurable TTL.
- Treat transcripts, chat, titles and comments as untrusted data.
- Model-generated timelines validated against JSON Schema and an effect allowlist.
- Never interpolate untrusted text into shell commands.
- Creator/streamer OAuth tokens remain server-side in secrets.
- No stream key or creator password is requested.
- Human approval is required for final acceptance; publishing functionality is absent.

## Cost strategy

- Short native clips first (Twitch/Kick), then full VOD analysis.
- For long videos, use chunked proxy analysis and low-resolution frame sampling.
- CPU for media probe, initial segmentation and simple transforms; GPU only for selected AI tasks.
- Use local/open-weight ASR and TTS when quality is acceptable.
- Display estimated Modal compute, storage and egress.
- No always-on monitoring by default in manual-capture mode.
