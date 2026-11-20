# Modal deployment

Modal hosts the Clipro FastAPI control plane and the short-lived media workers. The API is an autoscaling HTTPS ASGI endpoint; the probe worker is a separate function with its own compute profile.

## Required secrets

Create these two Modal Secrets from the Modal dashboard at https://modal.com/secrets or with the Modal CLI. Use the same Modal Environment for both apps.

### \`clipro-api-secrets\`

- \`SUPABASE_URL\`
- \`SUPABASE_JWT_AUDIENCE=authenticated\`
- \`DATABASE_URL\`
- \`DATABASE_SSL=true\`
- \`R2_ACCOUNT_ID\`
- \`R2_ACCESS_KEY_ID\`
- \`R2_SECRET_ACCESS_KEY\`
- \`R2_BUCKET_NAME\`
- \`CLIPRO_WEB_ORIGINS\` (local development and the Vercel production/preview origin)
- \`CLIPRO_MODAL_DISPATCH_ENABLED=false\` for the first API deployment; enable only after the worker is deployed
- \`CLIPRO_MODAL_APP_NAME=clipro-workers\`
- \`CLIPRO_MODAL_PROBE_FUNCTION=probe_asset\`
- \`MODAL_TOKEN_ID\`
- \`MODAL_TOKEN_SECRET\`

The Modal token lets the API container spawn jobs in the separate worker app. Create a dedicated token for the Clipro workspace and keep it only in this Secret.

### \`clipro-worker-secrets\`

- \`DATABASE_URL\`
- \`R2_ACCOUNT_ID\`
- \`R2_ACCESS_KEY_ID\`
- \`R2_SECRET_ACCESS_KEY\`
- \`R2_BUCKET_NAME\`

Never commit secret values, paste them into chat, or place them in browser environment variables.

## Deploy order

1. Apply the Supabase migrations in numeric order.
2. Create the private Cloudflare R2 bucket, bucket-scoped API token and required CORS policy.
3. Create both Modal Secrets described above.
4. From a cloud development shell at the repository root, authenticate the Modal CLI and deploy the media worker:

       python -m pip install --upgrade modal
       python -m modal setup
       modal deploy infra/modal/clipro_workers.py

5. Deploy the API:

       modal deploy infra/modal/clipro_api.py

6. Copy the HTTPS URL printed for the \`fastapi_app\` web endpoint. Set it as \`NEXT_PUBLIC_CLIPRO_API_URL\` in the Next.js/Vercel environment.
7. Set \`CLIPRO_WEB_ORIGINS\` in \`clipro-api-secrets\` to the exact web origins (for local development include \`http://localhost:3000\`; add the Vercel domain after deployment), then redeploy the API.
8. Confirm \`/healthz\` returns \`{"status":"ok","service":"clipro-api"}\`.
9. Deploy the Next.js app from \`apps/web\` on Vercel and configure its Supabase URL, publishable key and API URL.
10. After the API and worker are deployed and tested, update \`CLIPRO_MODAL_DISPATCH_ENABLED=true\` in the API Secret and redeploy the API.

The API can be deployed before the worker with dispatch disabled. Finalizing an upload will store it and leave its probe job queued. Do not enable dispatch before the worker exists and the API Modal token is configured.

## Worker: \`clipro-workers\`

- Function: \`probe_asset\`
- Image: Debian Slim + FFmpeg + Python 3.12
- Resources: 2 CPU, 4 GiB RAM, 50 GiB ephemeral disk, 30-minute timeout
- Retries: one retry for transient infrastructure failures
- Max containers: 2

The probe function downloads the exact private R2 object, runs ffprobe, computes SHA-256 and creates a thumbnail. The analysis function uses faster-whisper small for local transcription and Qwen2.5-VL-3B-Instruct on a T4 GPU to inspect sampled frames and transcript, returning ranked highlight timestamps. Neither function downloads platform URLs or public VODs.

## API: \`clipro-api\`

- Function: \`fastapi_app\`
- Image: Python 3.12 with API requirements
- Resources: 1 CPU, 2 GiB RAM, 15-minute request timeout
- Autoscaling with a short scale-down window

The API verifies Supabase JWTs, checks workspace membership, handles upload-session state and signs R2 multipart requests. It never proxies video bytes.

## Database connection string

From the Supabase Connect dialog, choose the Session pooler connection string when you need IPv4-compatible connectivity. Copy the full URI and replace only its password placeholder. The API strips the libpq \`sslmode\`/pooler hints and applies TLS with asyncpg. Keep the password URL-encoded if it contains reserved characters.

## Operational notes

- R2 remains durable media storage. Modal ephemeral disk is temporary scratch space for one job.
- Configure an R2 lifecycle rule to abort incomplete multipart uploads after the upload-session TTL.
- Keep the bucket private and use short-lived presigned URLs.
- Keep API token and R2/Postgres credentials out of the Next.js public environment.
- Do not enable always-on live stream monitoring in the manual-capture MVP.
