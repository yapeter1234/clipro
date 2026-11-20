# Clipro

**Clipro is a private, single-operator AI clipping and video-editing workspace.** It has no public registration, user directory, teams, invitations or billing. The first campaign is DiegoLoveless's Twitch GTA campaign, while the editing engine remains reusable for other creators, platforms, campaigns and ordinary uploaded videos.

## Operating workflow

1. The operator uploads a permitted native clip or authorized video file.
2. Clipro stores the source privately and starts an automated processing job.
3. A video-capable AI agent analyzes the actual video and audio, finds candidate moments, compares context and selects the strongest highlights.
4. The agent returns timestamped clip selections and a structured editing plan.
5. Clipro's editing tools execute the plan: cuts, captions, hooks, reframing, motion graphics, transitions, music/SFX and audio mixing.
6. Automated quality checks inspect the rendered output; the agent can request targeted revisions.
7. Clipro presents the finished MP4 and a review/quality report for the operator to download.

The first AI provider candidate is **Google Gemini 3.8 Flash**, using its direct video-input capability and free API tier where available. Provider access is isolated behind an adapter so we can switch models without changing the editing engine. Free-tier availability, quotas and terms are not guaranteed. Google's unpaid tier may use submitted content to improve its products and may involve human review; do not submit sensitive, confidential or private footage under that tier. See [Google's pricing](https://ai.google.dev/gemini-api/docs/pricing), [video understanding](https://ai.google.dev/gemini-api/docs/video-understanding) and [terms](https://ai.google.dev/gemini-api/terms).

The agent does not render pixels by itself. It understands the source, chooses exact timestamps and authors a validated edit plan; deterministic media tools execute those edits and encode the final video.

**Publishing is deliberately out of scope.** No social account integrations, auto-posting, scheduling or automatic engagement actions.

## Privacy and access

- One operator; no public registration or multi-user workspace model.
- The hosted dashboard/API should have a simple private access restriction.
- Private media storage; no public buckets or public media URLs.
- All provider, database, storage and Modal credentials remain server-side.
- Human review remains available before any finished video is published.
- No publishing endpoint or publishing credentials.

## Source acquisition rules

- Twitch: use permitted viewer-native clips created and downloaded manually when channel settings allow.
- Kick: use permitted viewer-native clips created and downloaded manually when available.
- YouTube: a Clip URL is a reference, not a downloadable MP4; custom editing requires an authorized source file.
- A public stream URL is never treated as a downloadable video file.
- No access-control bypass, undocumented playback extraction or unauthorized full-VOD downloading.

## Editing target

Default short-form output: 9:16, 1080x1920, source-matched or 30 fps where appropriate. The pipeline supports:
- context-preserving hooks and payoff;
- accurate word-synchronized captions and animated typography;
- gameplay/facecam layouts and smart reframing;
- purposeful transitions, zooms, punch-ins and motion graphics;
- optional original narration;
- properly licensed music and sound effects;
- audio ducking, normalization and technical/editorial quality checks.

The same timeline schema and renderer support stream clips and ordinary uploaded videos.

## Planned stack

| Layer | Technology |
|---|---|
| Private dashboard | Next.js + Uppy |
| API/control plane | FastAPI |
| Media storage | Cloudflare R2 (Google Drive may be optional archive/import later) |
| Cloud execution | Modal |
| Video understanding / agent | Gemini 3.8 Flash free tier initially, subject to quotas and data-use trade-offs |
| Local media signals | FFmpeg/ffprobe, faster-whisper/WhisperX, VAD, scene detection and visual sampling |
| Edit-plan contract | Versioned JSON timeline and strict tool schema |
| Motion graphics | Remotion, subject to license eligibility |
| Rendering | FFmpeg |
| Delivery | Private preview and downloadable MP4 |

## Development status

The current feature branch has browser upload, R2 multipart handling, Postgres asset/job records and a Modal media-probe worker. It still contains Supabase Auth and workspace-membership assumptions. Those are legacy scaffolding and must be removed. The initial private release does not require Supabase.

Not yet implemented: private single-operator refactor, Gemini video agent, highlight-selection pipeline, edit-plan tool execution, professional rendering, output review/download and end-to-end cloud integration.

See [ROADMAP.md](docs/ROADMAP.md), [ARCHITECTURE.md](docs/ARCHITECTURE.md), [M1 media ingestion ADR](docs/ADR_001_MEDIA_INGESTION.md), and [tooling research](docs/TOOLING_RESEARCH.md).

- Campaign-specific rules: [DiegoLoveless GTA profile](docs/campaigns/diego-loveless-gta6.md)
- Source policy: [Source acquisition guide](docs/INGESTION_NO_OBS.md)
- Browser capture steps: [Twitch, Kick and YouTube](docs/SOURCE_CAPTURE_GUIDE.md)
- Generic campaign template: [config/campaigns/template.json](config/campaigns/template.json)
- Editing rules: [Editing style guide](docs/EDITING_STYLE_GUIDE.md)
- Security: [Security requirements](docs/SECURITY.md)
- Timeline schema: [packages/timeline/schema.json](packages/timeline/schema.json)

## License and third-party code

Any reused third-party code must be reviewed file-by-file, retain required license notices and be recorded in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Platform Terms, media permissions, model/voice licenses and music/SFX rights remain separate requirements.
