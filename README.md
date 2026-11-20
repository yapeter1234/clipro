# Clipro

**Clipro is a private, single-operator AI clipping and video-editing workspace.** It is used by one operator with ChatGPT assisting the editorial workflow. It is not a public SaaS product and has no public registration, user directory, teams, invitations, or billing.

The first campaign is DiegoLoveless's Twitch GTA campaign, but the editing engine remains reusable for other creators, platforms, campaigns, and ordinary uploaded videos.

## Operating workflow

1. The operator manually creates/downloads a permitted native clip or supplies an authorized video file.
2. The operator uploads the source into the private Clipro workspace.
3. Clipro creates a processing pack: transcript with timestamps, audio cues, candidate ranges and visual contact sheets extracted from the source.
4. The operator shares that pack in this ChatGPT conversation. ChatGPT is the editorial brain: it selects moments, explains the rationale and returns a versioned edit-plan JSON. No separate model API key is required for this chat-based workflow.
5. The operator imports the edit plan into Clipro; the deterministic renderer creates the MP4 with captions, motion, reframing, sound design and campaign-specific treatment.
6. The operator shares the preview or QA report here for editorial review and revisions.
7. The operator downloads the approved result and publishes it manually, if desired.

ChatGPT is not callable from the deployed Vercel app using the user's ChatGPT subscription. The handoff between the app and this conversation is explicit (analysis pack into chat; edit plan back into the app). No separate generative-model API is part of the initial workflow.

**Publishing is deliberately out of scope.** No social account integrations, auto-posting, scheduling, or automatic engagement actions.

## Privacy and access

- One operator; no public sign-up or multi-user workspace model.
- The hosted dashboard and API must be protected by a private access layer (Cloudflare Access or equivalent allowlisted identity gate).
- Private R2 media storage; no public buckets or public media URLs.
- Server-side secrets only; never put database, storage or Modal credentials in browser bundles.
- Human approval is required before any finished video is considered final.
- No publishing endpoint or publishing credentials.

## Source acquisition rules

- Twitch: use permitted viewer-native clips created and downloaded manually when channel settings allow it.
- Kick: use permitted viewer-native clips created and downloaded manually when available.
- YouTube: a Clip URL is a reference, not a downloadable MP4; custom editing requires an authorized source file.
- A public stream URL is never treated as a downloadable video file.
- No access-control bypass, undocumented playback extraction, or unauthorized full-VOD downloading.

## Editing target

Default short-form output: 9:16, 1080x1920, source-matched or 30 fps where appropriate. The pipeline should support:
- context-preserving hooks and payoff;
- accurate word-synchronized captions and animated typography;
- gameplay/facecam layouts and smart reframing;
- purposeful transitions, zooms, punch-ins and motion graphics;
- optional original narration;
- properly licensed music and sound effects;
- audio ducking, normalization and technical/editorial quality checks.

The same timeline schema and renderer must support stream clips and ordinary uploaded videos.

## Planned stack

| Layer | Technology |
|---|---|
| Private dashboard | Next.js + Uppy |
| API/control plane | FastAPI |
| Metadata | Single-operator job manifests (database deferred unless needed) |
| Private access gate | Cloudflare Access or equivalent |
| Media storage | Cloudflare R2 |
| Cloud execution | Modal |
| Analysis pack | FFmpeg/ffprobe, speech transcription, VAD/audio cues and visual contact sheets |
| Editorial plan | ChatGPT-generated versioned JSON returned through this conversation |
| Voiceover | Kokoro or another appropriately licensed TTS model |
| Motion graphics | Remotion, subject to license eligibility |
| Rendering | FFmpeg |
| Timeline | Versioned JSON schema |

## Development status

The current M1 branch contains browser uploads, R2 multipart handling, Postgres asset/job records and a Modal media-probe worker. It still contains Supabase Auth and workspace-membership assumptions. Those are legacy scaffolding and must be removed. Supabase is no longer a required dependency for the first private release.

Not yet implemented: analysis-pack generation, ChatGPT handoff/import, edit-plan validation, professional rendering, finished-video review/download and the private access gate. Cloud resources have not yet been configured or verified against the operator's accounts.

See [ROADMAP.md](docs/ROADMAP.md), [ARCHITECTURE.md](docs/ARCHITECTURE.md), [M1 media ingestion ADR](docs/ADR_001_MEDIA_INGESTION.md), and [tooling research](docs/TOOLING_RESEARCH.md).

- Campaign-specific rules: [DiegoLoveless GTA profile](docs/campaigns/diego-loveless-gta6.md)
- Source policy: [Source acquisition guide](docs/INGESTION_NO_OBS.md)
- Browser capture steps: [Twitch, Kick and YouTube](docs/SOURCE_CAPTURE_GUIDE.md)
- Generic campaign template: [config/campaigns/template.json](config/campaigns/template.json)
- Editing rules: [Editing style guide](docs/EDITING_STYLE_GUIDE.md)
- Security: [Security requirements](docs/SECURITY.md)
- Timeline schema: [packages/timeline/schema.json](packages/timeline/schema.json)

## License and third-party code

Clipro is a new implementation. Any reused third-party code must be reviewed file-by-file, retain required license notices and be recorded in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Platform Terms, media permissions, model/voice licenses and music/SFX rights remain separate requirements.
