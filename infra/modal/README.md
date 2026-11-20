# Modal deployment

Modal hosts Clipro's public FastAPI control plane and serverless media workers. The API is public in prototype mode: there is no user password, browser session, Supabase Auth, or shared Clipro API signing secret.

## Required Modal Secrets

Create the following two Modal Secrets in the same Modal Environment.

### clipro-api-secrets

- DATABASE_URL
- DATABASE_SSL=true
- R2_ACCOUNT_ID
- R2_ACCESS_KEY_ID
- R2_SECRET_ACCESS_KEY
- R2_BUCKET_NAME
- CLIPRO_WEB_ORIGINS=*
- CLIPRO_MODAL_DISPATCH_ENABLED=false for first deployment; enable after workers are deployed
- CLIPRO_MODAL_APP_NAME=clipro-workers
- CLIPRO_MODAL_PROBE_FUNCTION=probe_asset
- CLIPRO_MODAL_ANALYSIS_FUNCTION=analyze_asset
- MODAL_TOKEN_ID
- MODAL_TOKEN_SECRET

The Modal token is infrastructure-to-infrastructure access used by FastAPI to spawn worker calls in the separate Modal app. It is not a Clipro user API password. Keep it in this server-side Modal Secret.

### clipro-worker-secrets

- DATABASE_URL
- R2_ACCOUNT_ID
- R2_ACCESS_KEY_ID
- R2_SECRET_ACCESS_KEY
- R2_BUCKET_NAME

These are service credentials, not user login credentials. Never place them in browser-exposed environment variables or commit their values.

## Deploy order

1. Create the Postgres project and apply all repository migrations in numeric order.
2. Create a private Cloudflare R2 bucket, bucket-scoped API token and browser CORS policy for the Vercel domain.
3. Create both Modal Secrets above.
4. From any authenticated deployment terminal or CI job, deploy the workers:

       python -m pip install --upgrade modal
       python -m modal setup
       modal deploy infra/modal/clipro_workers.py

5. Deploy the API:

       modal deploy infra/modal/clipro_api.py

6. Copy the HTTPS URL printed for fastapi_app. Set it as CLIPRO_API_URL in Vercel.
7. Confirm /healthz returns {"status":"ok","service":"clipro-api"}.
8. After confirming the worker app is deployed and the API Modal credentials work, set CLIPRO_MODAL_DISPATCH_ENABLED=true in clipro-api-secrets and redeploy the API.
9. Deploy the Next.js app from apps/web on Vercel. Only CLIPRO_API_URL is required by the web app.

## Worker: clipro-workers

- probe_asset: downloads an R2 source, runs ffprobe, computes SHA-256 and creates a thumbnail.
- analyze_asset: transcribes audio locally with faster-whisper small, samples up to 18 frames, runs Qwen2.5-VL-3B-Instruct on a T4 GPU, and stores ranked highlight timestamps in the processing job.

Neither worker downloads platform URLs or public VODs. Workers fetch only the R2 object identified by the asset row in Postgres.

## API: clipro-api

- FastAPI ASGI endpoint deployed on Modal.
- Public HTTP endpoints; no user account or bearer token required.
- Uses one internal shared workspace identity to satisfy current ownership columns in the prototype schema.
- Signs short-lived R2 multipart operations and dispatches jobs to Modal workers.
- Never proxies video bytes; the browser uploads multipart chunks directly to R2.

## Operational notes

- R2 remains durable media storage. Modal ephemeral disk is temporary scratch space for one job.
- Keep the R2 bucket private; browser uploads use short-lived signed operations.
- The app is intentionally public and has no per-user workspace isolation, quotas, or abuse controls yet. Anyone with the URL can submit work and consume configured storage/GPU resources.
- Do not enable always-on live stream monitoring in the manual-source prototype.
- The analysis path returns ranked highlight timestamps. MP4 rendering/export is a separate implementation milestone.
