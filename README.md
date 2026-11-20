# Clipro

**Clipro is a private, single-operator AI clipping and video-editing workspace.** It is used by one operator with ChatGPT assisting the editorial workflow. It is not a public SaaS product and has no public registration, user directory, teams, invitations, or billing.

The first campaign is DiegoLoveless's Twitch GTA campaign, but the editing engine remains reusable for other creators, platforms, campaigns, and ordinary uploaded videos.

## Operating workflow

1. The operator manually creates/downloads a permitted native clip or supplies an authorized video file.
2. The operator uploads the source into the private Clipro workspace.
3. Clipro probes, transcribes, analyzes and ranks candidate moments.
4. The AI editorial workflow proposes the strongest moment and a detailed edit plan.
5. The rendering pipeline creates a polished video with captions, motion, reframing, sound design and campaign-specific treatment.
6. The operator reviews the preview and can request changes.
7. The operator downloads the approved result and publishes it manually, if desired.

ChatGPT can help select moments, shape the edit, review outputs and iterate when the operator shares footage or results. It does not silently monitor livestreams or run in the background without an active configured workflow.

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
| Metadata | PostgreSQL (Supabase Postgres may be retained without Supabase Auth) |
| Private access gate | Cloudflare Access or equivalent |
| Media storage | Cloudflare R2 |
| Cloud execution | Modal |
| Analysis | FFmpeg/ffprobe, faster-whisper/WhisperX, VAD and visual sampling |
| Editorial plan | Provider-neutral structured JSON |
| Voiceover | Kokoro or another appropriately licensed TTS model |
| Motion graphics | Remotion, subject to license eligibility |
| Rendering | FFmpeg |
| Timeline | Versioned JSON schema |

## Development status

The current M1 branch contains a working foundation for browser uploads, R2 multipart handling, Postgres asset/job records and a Modal media-probe worker. Its current implementation still contains Supabase Auth and workspace-membership assumptions. Those are legacy scaffolding and must be refactored before deployment to the private single-operator model.

Not yet implemented: highlight analysis, editorial decision-making, professional edit-plan generation, full rendering, finished-video review/download, and the private access-gate integration. Cloud resources have not yet been configured or verified against the operator's accounts.

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
