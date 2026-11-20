# Roadmap and acceptance criteria

## M0 — prototype infrastructure
- [x] Repository scaffold, timeline schema and campaign/style architecture.
- [x] Define manual source acquisition boundaries for Twitch/Kick/YouTube.
- [x] Browser upload dashboard and Uppy multipart upload foundation.
- [x] R2 multipart orchestration and server-side object verification.
- [x] Modal media-probe worker and durable job records.
- [ ] Configure and deploy Vercel dashboard, Modal API/workers, Postgres and R2.
- [ ] Verify an authorized video can be uploaded and probed end-to-end.

**Exit:** public prototype accepts an authorized upload, stores it, validates it on Modal and displays its metadata.

## M1 — AI highlight discovery
- [x] Local Whisper transcription with faster-whisper small.
- [x] Sampled-frame visual analysis with Qwen2.5-VL-3B-Instruct on Modal T4.
- [x] Durable highlight-analysis processing job and API dispatch.
- [x] Dashboard button, progress, retry and candidate timestamp display.
- [ ] Deploy and verify first real inference run; measure GPU time and quality.
- [ ] Improve candidate boundary precision with denser sampling and audio cues.
- [ ] Add candidate selection and editable in/out points.

**Exit:** user uploads a video and receives useful, reviewable candidate highlights.

## M2 — actual clipping and rendering
- [ ] Add a clip-render job type and Modal FFmpeg rendering worker.
- [ ] Render selected in/out points to 9:16 vertical 1080x1920 MP4.
- [ ] Add safe crop/reframe options for gameplay and facecam.
- [ ] Generate thumbnail and store output in R2.
- [ ] Show rendered MP4 preview and download link.
- [ ] Add basic captions from transcript and user-selectable caption style.

**Exit:** user selects a highlight and receives a playable/downloadable vertical MP4.

## M3 — quality improvements
- [ ] Word-level caption timing and animated typography.
- [ ] Context-aware hooks and title treatments without misrepresenting events.
- [ ] Purposeful transitions, zooms, punch-ins and motion graphics.
- [ ] Audio ducking, normalization and final audio QA.
- [ ] Review report and bounded re-render controls.

**Exit:** rendered clips are polished and pass technical QA.

## M4 — broader source support
- [ ] Generic authorized video upload independent of streaming platform.
- [ ] Twitch/Kick viewer-native capture guidance.
- [ ] YouTube Clip reference and authorized-file workflow.
- [ ] Long-video segmentation and source-range selection.

**Exit:** the same tool handles stream-derived clips and ordinary uploaded videos.

## Explicit prototype decisions
- Public access: no user login, passwords, sessions, API bearer token or account system.
- No Supabase Auth. Postgres is currently used only for durable metadata and job state.
- R2 remains media storage; Modal ephemeral disk is temporary job scratch space.
- Infrastructure credentials remain server-side and are not user-access controls.
- No automatic social publishing.
- No arbitrary URL scraping or access-control bypass.
- Public access currently has no quotas or abuse protection; anyone can consume configured compute/storage resources.
