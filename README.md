# Clipro

**Clipro is a multi-streamer, multi-platform AI clipping and short-form video editing studio.**

It accepts native clips captured from live streams or past broadcasts, plus creator/campaign-authorized uploaded videos. It analyzes the footage, selects or improves moments, creates a fully edited short-form video, and returns it to the user for review and manual publishing.

Clipro is not a Diego-only tool. DiegoLoveless's Twitch GTA campaign is the first campaign profile used to validate the workflow.

## Product workflow

1. Select a streamer and optional campaign/style profile.
2. Choose source platform: Twitch, Kick or YouTube.
3. Choose source type: live stream, past broadcast/VOD or uploaded video.
4. Create/download a supported native clip or provide an authorized video file.
5. Upload the source file in the browser.
6. Clipro analyzes, selects moments, writes an edit plan, creates the video and performs quality checks.
7. User previews, approves, downloads and publishes manually.

**No automatic publishing.** Clipro does not post videos to TikTok, Instagram, YouTube or any other social platform.

## Source acquisition rules

- Twitch: logged-in viewers can create clips from live streams and VODs (5–60 seconds) when channel settings allow it; they can download clips they created from Clips Manager.
- Kick: viewers can create clips from live streams and VODs (10–180 seconds) and download clips they created.
- YouTube: Clips are public 5–60-second references/loops, not a general MP4 export. Live Clips have DVR and archival availability limits. For custom editing, upload an authorized creator/campaign source file.
- A public stream URL is not treated as a downloadable video file.
- Full VOD downloads from another creator are not assumed or attempted.
- Direct creator relay is an optional future mode, not required for the first pilot.

## Editing output

Target profile: 9:16, 1080x1920, with source-matched or 30 fps output where appropriate. The editor can add:
- context-preserving hooks and story structure;
- accurate word-synchronized captions;
- kinetic text and campaign CTA overlays;
- gameplay/facecam layouts and reframing;
- purposeful transitions, zooms, punch-ins and motion graphics;
- optional original narrator voiceover;
- licensed music and sound effects;
- audio ducking, normalization and quality checks.

The editing engine is source-agnostic. The future manual timeline editor will use the same timeline project schema and renderer.

## Planned stack

| Layer | Technology |
|---|---|
| Cloud execution | Modal |
| Backend | Python, FastAPI |
| Browser UI | Next.js |
| Media analysis | FFmpeg/ffprobe, OpenCV, faster-whisper, Silero VAD |
| Editorial plan | Provider-neutral structured JSON; local model first |
| Voiceover | Kokoro or another appropriately licensed TTS model |
| Motion graphics | Remotion |
| Rendering | FFmpeg |
| Metadata | PostgreSQL when multi-user; SQLite for local prototype only |
| Media artifacts | Object storage abstraction / Modal Volume for temporary worker files |

## Development status

See [ROADMAP.md](docs/ROADMAP.md) and [ARCHITECTURE.md](docs/ARCHITECTURE.md).

- Campaign-specific rules: [DiegoLoveless GTA profile](docs/campaigns/diego-loveless-gta6.md)
- Source policy: [Source acquisition guide](docs/INGESTION_NO_OBS.md)
- Browser capture steps: [Twitch, Kick and YouTube](docs/SOURCE_CAPTURE_GUIDE.md)
- Generic campaign template: [config/campaigns/template.json](config/campaigns/template.json)
- Generic streamer profile: [config/streamers/template.json](config/streamers/template.json)
- Streamer/brainrot style: [config/styles/streamer-brainrot.json](config/styles/streamer-brainrot.json)
- Editing rules: [Editing style guide](docs/EDITING_STYLE_GUIDE.md)
- Security: [Security requirements](docs/SECURITY.md)
- Timeline schema: [packages/timeline/schema.json](packages/timeline/schema.json)

## License and third-party code

Clipro is a new implementation. Any reused third-party code must be reviewed file-by-file, retain required license notices and be recorded in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Platform Terms, media permissions, model/voice licenses and music/SFX rights remain separate requirements.
