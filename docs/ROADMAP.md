# Roadmap and acceptance criteria

## M0 — repository and contracts

- [x] Initialize repository and product README.
- [ ] Define versioned timeline schema.
- [ ] Document system boundaries, permission model and data retention.
- [ ] Add lint/type/test workflow.
- [ ] Add a deterministic test fixture (synthetic media; no third-party stream).

**Exit:** schema validates sample projects; CI checks JSON and Python formatting/type tests.

## M1 — Diego Twitch live-VOD clip acquisition (no OBS)

- [x] Record the no-OBS Twitch VOD clip strategy and required scope.
- [x] Add initial official Twitch Helix client for live status, VOD listing, VOD clip creation, polling, and clip download URL lookup.
- [ ] Confirm Diego/campaign permission and add the user's Twitch account as a channel Editor, if accepted.
- [ ] Register a Twitch Developer application and configure the OAuth callback.
- [ ] Implement token validation, encrypted token storage and the `editor:manage:clips` scope flow.
- [ ] Find the active stream VOD and map detected moments to VOD offsets.
- [ ] Monitor approved chat/event signals and generate candidate timestamps.
- [ ] Request VOD clips, poll creation, fetch temporary media URLs promptly and store source media in temporary workspace storage.
- [ ] Add cleanup, retry, rate limit handling and cost quotas.
- [ ] Run integration tests against an authorized test channel.

**Exit:** a single authorized active Twitch broadcast can produce a downloadable source clip without an OBS feed, then pass through the shared editor. If Editor authorization is unavailable, use only permitted creator/campaign-supplied source files.

## M2 — platform metadata/chat adapters

- [ ] Twitch Helix/EventSub adapter (OAuth, signature verification, event subscription lifecycle).
- [ ] Kick public developer API/webhook adapter (OAuth/scopes and signature verification).
- [ ] YouTube Data API + Live Chat adapter (quota handling and reconnect).
- [ ] Normalize events to a provider-neutral schema.
- [ ] Test offline, private, restricted and permission-denied states.

**Exit:** the same monitor state model works for all three platforms; adapters report unsupported capabilities accurately.

## M3 — highlight intelligence

- [ ] Audio level/onset events.
- [ ] Silero VAD.
- [ ] Streaming/rolling faster-whisper transcription.
- [ ] Chat velocity, unique users and hype/emote signals.
- [ ] Scene-change/motion detection.
- [ ] Candidate windows with pre/post-roll.
- [ ] Overlap deduplication and explainable scoring.
- [ ] Optional selected-frame VLM evaluation.

**Exit:** on a labeled test recording, candidates contain meaningful context and evidence; false-positive rate is measurable.

## M4 — professional automatic editor

- [ ] Timeline project schema and validator.
- [ ] Source-segment trimming and beat-aware pacing.
- [ ] Vertical layouts, safe areas and facecam tracking.
- [ ] Remotion composition system.
- [ ] Animated captions and word emphasis.
- [ ] Hook/title cards and motion graphics.
- [ ] Optional separate narrator script + Kokoro TTS.
- [ ] Translation/subtitle tracks.
- [ ] Music/SFX library with rights metadata.
- [ ] Ducking, fades, loudness and true-peak checks.
- [ ] FFmpeg final render and output validation.
- [ ] QA report and reproducible render metadata.

**Exit:** one test candidate becomes a polished 9:16 video with synchronized captions, optional narration, purposeful motion/transitions, balanced audio and valid MP4. All inserted assets have rights metadata.

## M5 — approval dashboard

- [ ] Candidate queue and score evidence.
- [ ] Video player and review metadata.
- [ ] Approve/reject/regenerate actions.
- [ ] Download MP4, caption sidecar and project JSON.
- [ ] Server-side publish gate (publishing adapter remains disabled).
- [ ] User-visible usage and cost information.

**Exit:** no publish operation can succeed unless a human approval record exists for the exact render version.

## M6 — platform publishing (later)

- [ ] TikTok Content Posting API and app audit/authorization as required.
- [ ] YouTube upload integration.
- [ ] Instagram publishing integration.
- [ ] Campaign-specific metadata and disclosures.
- [ ] Per-platform upload status and retry/idempotency.

**Exit:** publishing only works after explicit human approval, with an immutable audit event.

## M7 — general video editor (later)

- [ ] Upload and media bins.
- [ ] Multi-track timeline UI.
- [ ] Trim, split, reorder, transitions and keyframes.
- [ ] Edit captions and voiceover.
- [ ] Replace/add b-roll, music and SFX.
- [ ] Versioned projects, autosave and undo/redo.
- [ ] Presets for Shorts, Reels, TikTok and horizontal videos.

**Exit:** uploaded non-live footage uses the same timeline and renderer as livestream clips.

## Pilot definition

The first end-to-end pilot is intentionally narrow:
1. One authorized creator and one platform feed.
2. One monitor process at a time.
3. A 9:16 output, initially 20–60 seconds unless campaign rules require otherwise.
4. AI produces a structured edit plan.
5. Renderer adds a clear hook, accurate captions, tasteful motion/transition treatment, optional narrator voiceover, licensed music/SFX and balanced audio.
6. User approves or rejects the rendered version.
7. No automatic publishing.
