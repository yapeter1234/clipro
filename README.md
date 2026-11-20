# Clipro

**Clipro is a private, single-operator AI clipping and video-editing workspace.** It has no public registration, user directory, teams, invitations or billing. The first campaign is DiegoLoveless's Twitch GTA campaign, while the editing engine remains reusable for other creators, platforms, campaigns and ordinary uploaded videos.

## Operating workflow

1. The operator uploads a permitted native clip or authorized video file.
2. Clipro stores the source privately and starts a processing job.
3. Modal provisions GPU inference for a self-hosted, open-weight multimodal model.
4. The AI agent inspects the video and audio, finds candidate moments, checks surrounding context and selects the strongest highlights.
5. The agent returns timestamped clip selections and a structured editing plan.
6. Clipro's editing tools execute the plan: cuts, captions, hooks, reframing, motion graphics, transitions, music/SFX and audio mixing.
7. The agent can inspect draft frames and QA results and request bounded revisions.
8. Clipro presents the finished MP4 and a review report for the operator to download.

## AI model and hosting

Initial model candidate: **Qwen3.6-35B-A3B**, an open-weight multimodal model with video/image understanding and tool-calling capability. Host the model on Modal GPUs using a compatible inference engine such as vLLM or SGLang, with a provider-neutral adapter so the model can be replaced after quality testing.

Clipro will preprocess long videos into bounded segments, timestamped transcripts and sampled frames. The agent uses those observations to reason about moments and calls a restricted set of editing tools. FFmpeg/Remotion perform the actual media transformations; the model does not regenerate the source footage.

No Gemini/OpenAI/other hosted model API key is required for this self-hosted path. Modal GPU compute is still metered. Modal compute credits and grant balances vary by account and can change; check the Modal billing dashboard for the current balance and expiration. Credits are limited, not unlimited free inference; usage beyond available credits is billed. Modal's separately hosted Model APIs are token-billed and are not covered by those compute credits. We intend to host our own weights rather than use those paid Model APIs.

## Publishing

Publishing is deliberately out of scope. No social account integrations, auto-posting, scheduling or automatic engagement actions. Finished videos are delivered privately for manual review and publication.

## Privacy and access

- One operator; no public registration or multi-user workspace model.
- Password login issues a signed HttpOnly session cookie; the browser never receives the session-signing secret.
- The same-origin Next.js proxy issues five-minute audience-restricted API tokens; FastAPI independently verifies them.
- Private media storage; no public buckets or public media URLs.
- All model, storage, Modal, database and signing credentials remain server-side.
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
| Media storage | Cloudflare R2 |
| Cloud execution and GPU hosting | Modal |
| Multimodal video agent | Qwen3.6-35B-A3B self-hosted on Modal (initial candidate) |
| Inference engine | vLLM or SGLang, subject to model compatibility testing |
| Local media signals | FFmpeg/ffprobe, speech transcription, VAD, scene detection and visual sampling |
| Agent tools | Restricted Python editing tools and validated timeline JSON |
| Motion graphics | Remotion, subject to license eligibility |
| Rendering | FFmpeg |
| Delivery | Private preview and downloadable MP4 |

## Development status

The private-operator migration replaces Supabase magic-link authentication with a password-protected Next.js session and independently verified FastAPI API tokens. A forward-only database migration consolidates legacy assets/jobs into one fixed operator workspace. Postgres and private R2 remain temporarily for durable metadata and resumable 20 GB multipart uploads; they are not required as product identity services. The Modal Volume alternative must pass upload-recovery and privacy tests before it replaces R2.

The first private-auth code path is now in the feature branch but still needs environment configuration, migration and deployment testing. Not yet implemented: self-hosted multimodal model deployment, video agent, highlight-selection/tool loop, professional rendering, output review/download and end-to-end cloud integration.

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
