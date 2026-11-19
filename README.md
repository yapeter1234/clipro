# Clipro

AI-assisted livestream clipping and short-form video production studio.

Clipro monitors one authorized live stream at a time, detects promising moments, creates fully edited vertical videos, and places every result in a human approval queue. A reusable timeline/rendering engine will later support ordinary uploaded-video editing as well as livestream-derived clips.

## Product principles

- **Authorized media only:** use creator-owned streams, explicit creator permission, or another clearly licensed input. Public chat access is not permission to download or commercially reuse a broadcast.
- **Human approval before publishing:** the system may detect, edit, render and prepare posts, but it must never publish without an explicit user approval action.
- **Video access is separate from platform events:** platform APIs provide live status and chat/event metadata; raw video ingestion must use an authorized source feed or a documented platform capability.
- **Editorial quality over effects volume:** transitions, motion graphics, narration, captions, sound design and music are selected to support the story—not added indiscriminately.
- **One reusable editing engine:** live clips and future manually uploaded videos use the same project/timeline schema and renderer.
- **Free-first and observable:** prefer open-source components and local inference; expose resource usage, processing time and estimated costs.

## Planned stack

| Layer | Planned technology |
|---|---|
| Cloud execution | Modal Functions and Sandboxes |
| Backend API | Python, FastAPI |
| Live video ingest | MediaMTX + FFmpeg, behind an authenticated ingress/relay |
| Platform adapters | Twitch Helix/EventSub, Kick Developer API/webhooks, YouTube Data/Live Streaming APIs |
| Speech transcription | faster-whisper |
| Voice activity detection | Silero VAD |
| Video analysis | OpenCV + selected-frame vision model |
| Editorial planning | Provider-agnostic structured JSON; local model first, optional paid API |
| Narration | Kokoro or another suitably licensed TTS engine |
| Motion graphics | Remotion |
| Media rendering | FFmpeg |
| Persistent metadata | SQLite for MVP; upgrade path to managed Postgres |
| Artifact storage | Modal Volume for MVP; object storage adapter for production |
| Review UI | Next.js |
| Authentication | Dashboard session auth; platform OAuth stored server-side only |

This stack is a proposal, not an assertion that every component is already integrated. The live ingest/network path and platform-specific permissions are explicit technical validation gates.

## Editing output

The first rendering profile targets 9:16 vertical video (1080x1920), with source-matched or 30 fps output where appropriate. A rendered clip can include:

- A context-preserving opening hook
- Dynamic, word-synchronized captions and emphasis
- Gameplay/facecam layouts and subject-aware reframing
- Purposeful cuts, zooms, punch-ins, wipes or other template-driven transitions
- Optional original narrator voiceover, separate from the streamer's voice
- Licensed or user-provided background music and sound effects
- Voice/music ducking, loudness normalization and audio quality checks
- Endings that preserve the payoff, plus optional campaign-specific CTA
- Platform-specific safe zones and export presets

No effect should be added merely for decoration. The editorial plan must preserve meaning and context.

## Initial milestone

**M0 — repository and architecture scaffold**

1. Define the timeline project schema and state machine.
2. Create a provider-neutral media ingestion interface.
3. Create platform adapter interfaces (not undocumented stream extractors).
4. Build a deterministic render pipeline using a supplied local test file.
5. Add a review queue; publishing remains disabled.

**M1 — authorized Twitch pilot**

1. Verify an authorized live video feed from a creator/stream owner.
2. Validate secure ingress to the worker.
3. Monitor Twitch live status/chat through official APIs.
4. Detect candidate moments and preserve pre/post-roll from a rolling buffer.
5. Render one complete, polished short and return it for approval.

Kick and YouTube adapters follow after the common ingest/render path is proven. Platform-specific capabilities and permissions must be validated independently.

## Repository map (planned)

```
apps/
  web/                  # Next.js review dashboard
services/
  api/                  # FastAPI control plane
  worker/                # detection and render orchestration
packages/
  timeline/              # shared edit/timeline schema
  renderer/              # Remotion compositions and FFmpeg pipeline
  platform-adapters/     # Twitch, Kick, YouTube metadata/chat adapters
infra/
  modal/                 # Modal app definitions and deployment config
docs/
  ARCHITECTURE.md
  ROADMAP.md
  SECURITY.md
```

## What is deliberately out of scope for the first pilot

- Monitoring multiple streams simultaneously
- Automatic publication to social platforms
- Undocumented scraping or bypassing access restrictions
- Voice cloning of streamers
- Full multi-track manual editor UI

These can be considered only after the one-stream authorized-input workflow works reliably.

## License and third-party code

Clipro is a new project. Any code reused from third-party repositories must be reviewed file-by-file, preserve applicable license notices, and be recorded in a third-party notices file. A tool's MIT license does not remove platform terms, media rights, model/voice licenses, or music rights obligations.
