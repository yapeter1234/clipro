# Clipro web studio

Next.js App Router UI for authenticated source intake.

## Environment

Copy .env.example to .env.local and configure NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY and NEXT_PUBLIC_CLIPRO_API_URL.

Only the Supabase publishable key is exposed to the browser. Keep R2 access credentials and Postgres connection credentials in the API/worker environment.

## Local development

From apps/web:

    npm install
    npm run dev

Configure Supabase Auth redirect URLs to include the local and deployed app origins, plus /auth/callback.

The upload surface uses Uppy S3 multipart callbacks to transfer video directly to private R2 via short-lived URLs issued by FastAPI. R2 CORS must allow the exact web origin and expose the ETag response header.

## Current boundary

The UI starts and completes multipart uploads after Supabase, Postgres, API and R2 are configured. Media probing, AI analysis and rendering are not yet connected.
