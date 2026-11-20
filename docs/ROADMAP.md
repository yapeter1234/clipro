# Roadmap and acceptance criteria

## M0 — source, campaign and timeline contracts
- [x] Repository scaffold, timeline schema and campaign/style architecture.
- [x] Define manual source acquisition boundaries.
- [x] Add source policy for Twitch/Kick/YouTube live and past broadcasts.
- [x] Add tests for platform source constraints.
- [x] Add ffprobe helper tests and media probe worker.
- [ ] Add end-to-end test against real Cloudflare R2, Postgres and Modal resources.

**Exit:** supported source files can be safely ingested and described independently of any creator/campaign.

## M1 — private single-operator foundation (refactor required)
- [x] Browser upload dashboard and Uppy 6 multipart upload integration.
- [x] R2 multipart orchestration and server-side object verification.
- [x] Durable asset/job records and Modal media-probe worker.
- [ ] Remove Supabase Auth, magic-link sign-in, user IDs, workspace tables/membership joins and multi-user RLS assumptions.
- [ ] Add a private access gate (prefer Cloudflare Access allowlist) for both dashboard and API; verify identity server-side.
- [ ] Replace workspace-scoped ownership with a single private library/project scope.
- [ ] Keep private storage, short-lived signed upload/download URLs and server-generated object keys.
- [ ] Configure and verify R2, Postgres, Modal and the access gate against real cloud accounts.
- [ ] Add asset preview/download and safe cleanup/retention.

**Exit:** only the allowlisted operator can open the dashboard/API, upload a permitted source, validate it in Modal and see the asset ready for analysis. No public registration exists.

## M2 — analysis and highlight selection
- [ ] Transcribe short clips with word-level timestamps.
- [ ] Chunk and analyze long authorized videos.
- [ ] Detect candidate moments using speech, audio energy/VAD and visual sampling.
- [ ] Rank moments by context, reaction, humor, payoff and campaign fit.
- [ ] Detect duplicates/reused moments and low-quality segments.
- [ ] Apply creator/game/topic campaign compliance gates.
- [ ] Return ranked candidate moments with timestamps, rationale and confidence.
- [ ] Provide an operator review/selection step before rendering.

**Exit:** Clipro recommends the strongest moments from a supplied source and explains why they are worth editing.

## M3 — professional editing and rendering
- [ ] Generate a structured, editable timeline JSON plan.
- [ ] Context-aware hook/title treatment without misrepresenting the source.
- [ ] Accurate animated word-synchronized captions.
- [ ] Purposeful transitions, zooms, punch-ins and motion graphics.
- [ ] Smart gameplay/facecam layout and reframing.
- [ ] Optional original narrator voiceover.
- [ ] Licensed music/SFX library and rights metadata.
- [ ] Voice/music ducking, normalization and final audio QA.
- [ ] Campaign CTA/hashtags and platform-specific export presets.
- [ ] Render final MP4 and attach a technical/editorial quality report.

**Exit:** a polished short-form MP4 is generated from an approved edit plan and passes automated QA.

## M4 — private review and delivery
- [ ] Preview finished render in the private dashboard.
- [ ] Approve, reject, request changes or regenerate.
- [ ] Download final MP4, captions and timeline JSON.
- [ ] Preserve project/edit revisions for iteration.
- [ ] Optional manual post URL and analytics notes entered by the operator.
- [ ] Enforce publication disabled server-side.

**Exit:** finished videos are delivered privately to the operator; nothing is published by Clipro.

## M5 — additional source adapters and generic editing
- [ ] Twitch viewer-native clip workflow guidance.
- [ ] Kick viewer-native clip workflow guidance.
- [ ] YouTube Clip reference and authorized-file workflow.
- [ ] Generic uploaded-video intake independent of streaming platform.
- [ ] Source-range selection and chunked analysis for long videos.
- [ ] Multi-track manual editing, captions, overlays, music/SFX and export revisions.

**Exit:** the same private tool handles stream-derived clips and ordinary uploaded video projects.

## Not in scope
- Public sign-up, multiple users, teams, invitations, roles or billing.
- Automatic publishing to TikTok, Instagram, YouTube or any destination.
- Automatic raw-video extraction from arbitrary public stream URLs.
- Twitch Editor role for Diego unless separately authorized.
- Unofficial download/scraping workarounds.
- Always-on livestream monitoring in the initial manual-source workflow.
- Making platform engagement/audience guarantees.
