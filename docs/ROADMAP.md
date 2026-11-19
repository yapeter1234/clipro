# Roadmap and acceptance criteria

## M0 — contracts and product structure
- [x] Repository scaffold, timeline schema and campaign/style architecture.
- [x] Define manual source acquisition boundaries.
- [x] Add source policy for Twitch/Kick/YouTube live and past broadcasts.
- [x] Add tests for platform source constraints.
- [ ] Add generic streamer/campaign/style profile CRUD.
- [ ] Add CI coverage for all API/worker modules and config JSON.
- [ ] Add test media fixtures and source probe.

**Exit:** a user can define a creator/campaign profile without changing code; source policies correctly describe live vs past video for each platform.

## M1 — browser source intake
- [ ] Add browser upload UI with resumable/chunked upload.
- [ ] Add source metadata form (platform, creator/channel, live/past/uploaded, source URL/clip URL, campaign, authorization).
- [ ] Add media probe (ffprobe) and file validation.
- [ ] Add source-range selector for long authorized VOD files.
- [ ] Add capture instructions and file-download guide per platform.
- [ ] Enforce no public-URL downloading in the backend.
- [ ] Add upload storage abstraction, checksum and TTL cleanup.

**Exit:** user can upload a manually downloaded Twitch/Kick clip or an authorized source file and start an editing job in a browser.

## M2 — universal analysis pipeline
- [ ] Transcribe and inspect complete short clips.
- [ ] Chunk and analyze long uploaded VODs.
- [ ] Detect highlights using ASR, audio energy/VAD and visual sampling.
- [ ] Add optional chat/event metadata as a signal, never as source media.
- [ ] Detect duplicate/reused moments.
- [ ] Add creator/game/topic campaign compliance gate.
- [ ] Return ranked moments with reason and timestamps.

**Exit:** the same analysis works for live-origin native clips and historical VOD files from any configured streamer.

## M3 — professional editing engine
- [ ] Remotion compositions and reusable style templates.
- [ ] Dynamic word-synchronized captions.
- [ ] Context-aware hook and title treatment.
- [ ] Purposeful transitions, zooms, punch-ins and motion graphics.
- [ ] Smart facecam/gameplay layout and reframe.
- [ ] Optional original narrator voiceover using Kokoro.
- [ ] Licensed music/SFX library and rights metadata.
- [ ] Voice/music ducking, normalization and final audio QA.
- [ ] CTA/hashtag overlays from campaign profile.
- [ ] FFmpeg final export and quality report.

**Exit:** output is a polished 9:16 MP4 with full editorial treatment, correct captions/CTA and campaign-specific rules.

## M4 — review dashboard
- [ ] Preview, approve/reject/regenerate/download.
- [ ] Expose timeline project and caption sidecar.
- [ ] Enforce publication disabled server-side.
- [ ] Record user-posted URL and live-since date.
- [ ] Remind user about campaign retention period.
- [ ] Collect post-publish metrics and analytics evidence.

**Exit:** every rendered clip stays private until the user downloads and publishes manually.

## M5 — additional source adapters
- [ ] Twitch viewer-native clip workflow documentation/instructions; optional Editor API remains disabled unless separately authorized.
- [ ] Kick viewer-native clip workflow documentation/instructions.
- [ ] YouTube Clip reference storage and authorized-file workflow.
- [ ] Optional creator-authorized direct relay for channels that provide it.
- [ ] Platform-specific capability tests and UI messages.

**Exit:** user can select Twitch, Kick or YouTube and is guided to a supported source method for live or past material.

## M6 — general manual editor
- [ ] Upload bins and multi-source projects.
- [ ] Multi-track timeline UI.
- [ ] Trim, split, reorder, transition and keyframe controls.
- [ ] Edit captions, title, CTA and voiceover.
- [ ] Add/replace licensed b-roll, music and SFX.
- [ ] Autosave, undo/redo and project revisions.
- [ ] Export presets for Shorts, Reels, TikTok and horizontal video.

**Exit:** ordinary uploaded videos and stream-derived clips use the same renderer.

## Not in scope
- Automatic publishing to TikTok, Instagram, YouTube or any other destination.
- Automatic raw-video extraction from arbitrary public stream URLs.
- Twitch Editor role for Diego.
- Unofficial download/scraping workarounds.
- Making platform engagement/audience guarantees.
