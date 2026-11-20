# Clipro web studio

Private Next.js App Router dashboard for one operator.

## Environment

Copy `.env.example` to `.env.local` and configure:

- `CLIPRO_OPERATOR_PASSWORD`: a long, unique operator password (20+ characters).
- `CLIPRO_SESSION_SECRET`: random 32-byte-or-stronger secret used only by Next.js.
- `CLIPRO_API_TOKEN_SECRET`: random secret shared between the Next.js server and the Modal FastAPI Secret.
- `CLIPRO_API_URL`: the Modal FastAPI base URL, server-side only.

Generate secrets with `openssl rand -hex 32`. Do not use a `NEXT_PUBLIC_` prefix for any of these values. Never commit `.env.local` or share secrets in chat.

## Local development

From `apps/web`:

    npm install
    npm run dev

The dashboard uses one password-protected HttpOnly session. The browser calls a same-origin Next.js API proxy; the proxy verifies the session and mints a five-minute audience-restricted bearer token for FastAPI. The API independently verifies that token. Permanent signing keys, Modal credentials, Postgres credentials and R2 credentials stay server-side.

## Large video uploads

Uppy 6 transfers video directly to the private R2 bucket using short-lived multipart URLs issued by FastAPI through the authenticated Next.js proxy. The full 20 GB file is not proxied through Vercel. R2 CORS must allow the exact web origin and expose the ETag response header.

Postgres and R2 are retained as the transitional durable metadata/storage path. Supabase Auth and magic-link login are no longer used. The Modal Volume storage alternative is a separate prototype and must pass interrupted-upload, resume, checksum, cross-container read and private-download tests before R2 is removed.

## Deployment security

Configure rate limiting for `/api/auth/login` at the hosting/WAF layer (for example, Vercel Firewall). Do not rely on an in-memory serverless rate limiter. Configure the same `CLIPRO_API_TOKEN_SECRET` value in the Vercel server environment and the Modal API Secret. Redeploy both sides after rotating it.

Media probing, AI analysis and rendering remain separate milestones; the current upload worker only validates media.
