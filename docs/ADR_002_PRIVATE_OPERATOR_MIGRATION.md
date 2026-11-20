# ADR-002: Private single-operator access and infrastructure migration

- Status: Accepted for implementation
- Date: 2026-11-19
- Supersedes: the Supabase Auth portion of ADR-001; the current R2 multipart path remains the compatibility baseline until its replacement passes an upload test.

## Context

Clipro is a private tool for one operator, not a public SaaS product. The current M1 implementation still assumes Supabase Auth, user-created workspaces, workspace membership, Postgres job records and Cloudflare R2. The browser obtains a Supabase access token and sends it directly to the FastAPI API.

The target experience should require no public registration, email magic links, teams, invitations, subscriptions or publishing integrations. The operator must not expose permanent service credentials in browser JavaScript, and protecting only the Vercel page is insufficient because the Modal API is independently reachable.

A 20 GB source upload also needs resumable, bounded requests. Replacing object storage with a shared filesystem without testing chunk persistence, concurrency, finalization, and private download behavior would risk losing the working upload path.

## Decisions

### 1. Operator authentication

- Replace Supabase magic-link login with one operator password configured as a server-side secret.
- Issue a signed, HttpOnly, Secure-in-production, SameSite=Lax session cookie with a bounded lifetime.
- Validate the session in the Next.js proxy and again in every server route that uses it.
- Provide a short-lived, audience-restricted API bearer token to the browser only when it needs to call FastAPI. Never expose the signing secret or any permanent Modal, database, or storage credential.
- FastAPI independently verifies the API token signature, issuer, audience, expiry and fixed operator identity. Requests without a valid token fail closed.
- Login must use constant-time secret comparison, generic failure messages, origin checks and deployment-level rate limiting. Do not claim an in-memory rate limiter is sufficient across serverless instances.
- Logout clears the session cookie. Rotating the signing secret invalidates existing sessions and API tokens.

### 2. Transitional metadata compatibility

- Remove Supabase Auth as the application's identity provider.
- Keep Postgres temporarily as the durable asset/job metadata store while the private auth migration is implemented and tested.
- Replace auth.users foreign-key assumptions with a fixed operator identity and one seeded private workspace. Keep membership checks as a single-operator ownership boundary until the data model is simplified.
- No browser Supabase client, Supabase JWT, magic-link callback, or workspace picker remains in the target UI.
- Postgres is a transitional dependency, not a product requirement. A later migration may replace it with a Modal-native metadata store only after persistence, concurrency, recovery and retention tests pass.

### 3. Media storage and large uploads

- Keep the R2 bucket private and keep the existing Uppy multipart design during the first auth migration.
- R2 credentials remain server-side. The browser receives only narrowly scoped, short-lived presigned multipart URLs after API authorization.
- Do not proxy an entire 20 GB file through Vercel or a single FastAPI request.
- Prototype Modal Volume storage separately using small, bounded chunks written to unique part files, explicit commit/reload, single-writer finalization, checksum verification, cleanup and a private download path.
- Modal Volumes do not provide distributed file locking; concurrent writes to the same file must be avoided. Do not use one shared SQLite database file as a multi-container concurrent write store without a serialization design.
- Only remove R2 after the Modal-only prototype passes interrupted-upload, retry/resume, cross-container read, checksum, private-download and cleanup tests on a representative large file.

### 4. Source rights and processing boundaries

- Preserve source permission confirmation, rights basis, manual/native source acquisition rules and URL-as-reference-only behavior.
- Never fetch arbitrary Twitch, Kick or YouTube playback URLs, bypass platform controls, or treat a public URL as permission.
- Keep publication disabled. Finished media is delivered privately for manual review.
- Keep the AI model and editing worker inaccessible except through typed, authenticated jobs. Model output never becomes arbitrary shell commands or URLs.

## Implementation sequence

1. Add operator session login/logout and server-side session verification to Next.js.
2. Add independent short-lived operator API-token verification to FastAPI.
3. Replace Supabase browser auth in the dashboard and upload client; seed the fixed operator/workspace metadata identity with a forward-only migration.
4. Test login, logout, expired/invalid token rejection, direct API access without a token, upload preflight, multipart retry/finalize, and existing source-rights tests.
5. Deploy and verify the compatibility path before removing unused Supabase Auth dependencies and callbacks.
6. Build and benchmark the Modal Volume upload/storage prototype independently. Keep R2 as rollback until all acceptance tests pass.
7. Simplify metadata persistence only after a durable single-operator alternative is demonstrated.

## Acceptance criteria

- Unauthenticated users cannot access the dashboard, upload endpoints, job endpoints or media delivery endpoints.
- A valid browser session does not expose a long-lived backend secret.
- Calling the Modal API directly without a valid short-lived token is rejected.
- Expired, malformed, wrong-audience and wrong-signature tokens are rejected.
- Upload permission checks and server-side media validation remain intact.
- A large upload can resume after interruption and finalization verifies actual stored bytes.
- Source media and renders remain private; no automatic publishing path exists.
- Infrastructure is not removed until the replacement passes the same acceptance tests.
