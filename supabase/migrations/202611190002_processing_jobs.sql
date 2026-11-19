-- Clipro M1b: durable serverless media-processing jobs.
-- Apply after 202611190001_m1_media_uploads.sql.

alter table public.media_assets
    add column if not exists probe_metadata jsonb,
    add column if not exists thumbnail_key text;

create table if not exists public.processing_jobs (
    job_id uuid primary key default gen_random_uuid(),
    workspace_id uuid not null references public.workspaces(workspace_id) on delete cascade,
    asset_id uuid not null references public.media_assets(asset_id) on delete cascade,
    job_type text not null check (job_type in ('media_probe')),
    status text not null check (status in ('queued', 'running', 'succeeded', 'failed', 'cancelled')),
    progress integer not null default 0 check (progress between 0 and 100),
    attempt_count integer not null default 0 check (attempt_count >= 0),
    modal_call_id text,
    dispatch_error text,
    error_message text,
    result_json jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    started_at timestamptz,
    completed_at timestamptz
);

create index if not exists processing_jobs_workspace_created_idx
    on public.processing_jobs(workspace_id, created_at desc);
create index if not exists processing_jobs_asset_idx
    on public.processing_jobs(asset_id, job_type, created_at desc);
create index if not exists processing_jobs_status_idx
    on public.processing_jobs(status, created_at);

alter table public.processing_jobs enable row level security;

drop policy if exists "members can read processing jobs" on public.processing_jobs;
create policy "members can read processing jobs" on public.processing_jobs
for select to authenticated
using (public.clipro_is_workspace_member(workspace_id));

grant select on public.processing_jobs to authenticated;
revoke insert, update, delete on public.processing_jobs from anon, authenticated;
