-- Clipro M1: workspaces, media assets and resumable upload sessions.
-- Apply to the Clipro Supabase project before enabling uploads.

create extension if not exists pgcrypto;

create table if not exists public.workspaces (
    workspace_id uuid primary key default gen_random_uuid(),
    name text not null,
    created_by uuid not null references auth.users(id) on delete cascade,
    created_at timestamptz not null default now()
);

create table if not exists public.workspace_memberships (
    workspace_id uuid not null references public.workspaces(workspace_id) on delete cascade,
    user_id uuid not null references auth.users(id) on delete cascade,
    role text not null check (role in ('owner', 'admin', 'editor', 'viewer')),
    created_at timestamptz not null default now(),
    primary key (workspace_id, user_id)
);
create index if not exists workspace_memberships_user_idx
    on public.workspace_memberships(user_id);

create table if not exists public.media_assets (
    asset_id uuid primary key default gen_random_uuid(),
    workspace_id uuid not null references public.workspaces(workspace_id) on delete cascade,
    uploaded_by uuid not null references auth.users(id),
    streamer_id text,
    campaign_id text,
    platform text not null check (platform in ('twitch', 'kick', 'youtube', 'upload')),
    source_kind text not null check (source_kind in ('live_stream', 'past_broadcast', 'uploaded_video')),
    acquisition_mode text not null check (acquisition_mode in ('viewer_native_clip_manual_download', 'authorized_source_file')),
    source_url text,
    original_filename text not null,
    declared_mime_type text not null,
    file_size_bytes bigint not null check (file_size_bytes > 0),
    storage_key text not null unique,
    checksum_sha256 text,
    duration_ms bigint,
    width integer,
    height integer,
    frame_rate_num integer,
    frame_rate_den integer,
    video_codec text,
    audio_codec text,
    rights_status text not null check (rights_status in ('creator_authorized', 'user_owned', 'licensed', 'public_domain', 'pending_review')),
    rights_notes text,
    permission_confirmed boolean not null default false,
    state text not null check (state in ('uploading', 'uploaded', 'probing', 'ready', 'rejected', 'aborted', 'failed')),
    created_at timestamptz not null default now(),
    completed_at timestamptz
);
create index if not exists media_assets_workspace_created_idx
    on public.media_assets(workspace_id, created_at desc);
create index if not exists media_assets_state_idx
    on public.media_assets(state);

create table if not exists public.upload_sessions (
    upload_session_id uuid primary key default gen_random_uuid(),
    asset_id uuid not null unique references public.media_assets(asset_id) on delete cascade,
    workspace_id uuid not null references public.workspaces(workspace_id) on delete cascade,
    uploaded_by uuid not null references auth.users(id),
    storage_upload_id text not null unique,
    storage_key text not null unique,
    status text not null check (status in ('uploading', 'completed', 'aborted', 'expired', 'failed')),
    expires_at timestamptz not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    completed_at timestamptz
);
create index if not exists upload_sessions_expiry_idx
    on public.upload_sessions(status, expires_at);

create or replace function public.clipro_create_personal_workspace()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
    new_workspace_id uuid;
    workspace_name text;
begin
    workspace_name := coalesce(
        nullif(trim(new.raw_user_meta_data ->> 'full_name'), ''),
        nullif(split_part(coalesce(new.email, 'Clipro user'), '@', 1), ''),
        'Clipro workspace'
    ) || '''s workspace';

    insert into public.workspaces(name, created_by)
    values (workspace_name, new.id)
    returning workspace_id into new_workspace_id;

    insert into public.workspace_memberships(workspace_id, user_id, role)
    values (new_workspace_id, new.id, 'owner');
    return new;
end;
$$;

drop trigger if exists on_auth_user_created_clipro_workspace on auth.users;
create trigger on_auth_user_created_clipro_workspace
after insert on auth.users
for each row execute procedure public.clipro_create_personal_workspace();

-- Backfill accounts created before this migration is applied.
do $$
declare
    auth_user record;
    new_workspace_id uuid;
    workspace_name text;
begin
    for auth_user in
        select u.id, u.email, u.raw_user_meta_data
        from auth.users u
        where not exists (
            select 1 from public.workspace_memberships wm where wm.user_id = u.id
        )
    loop
        workspace_name := coalesce(
            nullif(trim(auth_user.raw_user_meta_data ->> 'full_name'), ''),
            nullif(split_part(coalesce(auth_user.email, 'Clipro user'), '@', 1), ''),
            'Clipro workspace'
        ) || '''s workspace';

        insert into public.workspaces(name, created_by)
        values (workspace_name, auth_user.id)
        returning workspace_id into new_workspace_id;

        insert into public.workspace_memberships(workspace_id, user_id, role)
        values (new_workspace_id, auth_user.id, 'owner');
    end loop;
end;
$$;

-- SECURITY DEFINER avoids recursive RLS evaluation on workspace_memberships.
create or replace function public.clipro_is_workspace_member(target_workspace uuid)
returns boolean
language sql
stable
security definer
set search_path = public
set row_security = off
as $$
    select exists (
        select 1 from public.workspace_memberships wm
        where wm.workspace_id = target_workspace and wm.user_id = auth.uid()
    );
$$;
revoke all on function public.clipro_is_workspace_member(uuid) from public;
grant execute on function public.clipro_is_workspace_member(uuid) to authenticated;

alter table public.workspaces enable row level security;
alter table public.workspace_memberships enable row level security;
alter table public.media_assets enable row level security;
alter table public.upload_sessions enable row level security;

drop policy if exists "members can read workspaces" on public.workspaces;
create policy "members can read workspaces" on public.workspaces
for select to authenticated
using (public.clipro_is_workspace_member(workspace_id));

drop policy if exists "members can read memberships" on public.workspace_memberships;
create policy "members can read memberships" on public.workspace_memberships
for select to authenticated
using (public.clipro_is_workspace_member(workspace_id));

drop policy if exists "members can read media assets" on public.media_assets;
create policy "members can read media assets" on public.media_assets
for select to authenticated
using (public.clipro_is_workspace_member(workspace_id));

drop policy if exists "members can read upload sessions" on public.upload_sessions;
create policy "members can read upload sessions" on public.upload_sessions
for select to authenticated
using (public.clipro_is_workspace_member(workspace_id));

grant select on public.workspaces, public.workspace_memberships,
    public.media_assets, public.upload_sessions to authenticated;
revoke insert, update, delete on public.workspaces, public.workspace_memberships,
    public.media_assets, public.upload_sessions from anon, authenticated;
