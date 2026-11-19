# Modal deployment

Modal runs short-lived, autoscaling media workers. The first worker is a CPU-only media probe that downloads one already-authorized private R2 object, runs ffprobe, computes SHA-256 and stores a thumbnail. It does not inspect platform URLs or download a stream.

## Worker

- App: \`clipro-workers\`
- Function: \`probe_asset\`
- Image: Debian Slim + FFmpeg + Python 3.12
- Resources: 2 CPU, 4 GiB RAM, 50 GiB ephemeral disk, 30-minute timeout, max 2 containers
- Retries: one retry for transient infrastructure failures

The function uses Modal Secret \`clipro-worker-secrets\`, containing server-side \`DATABASE_URL\`, \`R2_ACCOUNT_ID\`, \`R2_ACCESS_KEY_ID\`, \`R2_SECRET_ACCESS_KEY\` and \`R2_BUCKET_NAME\`. Never put those values in GitHub or browser environment variables.

Deploy from the repository root after creating the secret:

    modal deploy infra/modal/clipro_workers.py

The API dispatch code is a separate step and requires Modal API authentication in the API environment. Do not claim worker dispatch is active until the app is deployed and the API's Modal credentials are configured.

## Required Modal resources

- \`clipro-workers\`: media probe, followed later by ASR, visual analysis, TTS and rendering.
- Keep probe, ASR, GPU vision and render functions separate so we only pay for the resources each stage needs.
- R2 remains durable media storage. Use Modal ephemeral disk only as bounded scratch space for one job.

## Future workers

- \`clipro-analyze\`: CPU-first chunking, VAD, PySceneDetect and transcription orchestration.
- \`clipro-asr\`: faster-whisper for word timestamps.
- \`clipro-vision\`: optional GPU reasoning only on selected windows.
- \`clipro-tts\`: original narration with an appropriately licensed voice.
- \`clipro-render\`: FFmpeg and, if commercial license eligibility is confirmed, Remotion.
- \`clipro-cleanup\`: TTL and expired multipart cleanup.

Never run always-on stream monitoring in the manual-capture MVP.
