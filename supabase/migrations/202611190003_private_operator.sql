-- Clipro private single-operator migration.
-- Removes the application's dependency on Supabase Auth users while retaining
-- Postgres as a transitional metadata store and preserving all existing assets/jobs.

begin;

drop trigger if exists on_auth_user_created_clipro_workspace on auth.users;
drop function if exists public.clipro_create_personal_workspace();

alter table public.workspaces
    drop constraint if exists workspaces_created_by_fkey;
alter table public.workspace_memberships
    drop constraint if exists workspace_memberships_user_id_fkey;
alter table public.media_assets
    drop constraint if exists media_assets_uploaded_by_fkey;
alter table public.upload_sessions
    drop constraint if exists upload_sessions_uploaded_by_fkey;

-- The app uses one stable internal operator UUID; it is not an auth.users row.
insert into public.workspaces (workspace_id, name, created_by)
values (
    '00000000-0000-4000-8000-000000000002',
    'Clipro Private Workspace',
    '00000000-0000-4000-8000-000000000001'
)
on conflict (workspace_id) do update
set name = excluded.name,
    created_by = excluded.created_by;

-- Consolidate legacy workspace data into the one private operator workspace.
update public.media_assets
set workspace_id = '00000000-0000-4000-8000-000000000002',
    uploaded_by = '00000000-0000-4000-8000-000000000001';

update public.upload_sessions
set workspace_id = '00000000-0000-4000-8000-000000000002',
    uploaded_by = '00000000-0000-4000-8000-000000000001';

update public.processing_jobs
set workspace_id = '00000000-0000-4000-8000-000000000002';

delete from public.workspace_memberships;
insert into public.workspace_memberships (workspace_id, user_id, role)
values (
    '00000000-0000-4000-8000-000000000002',
    '00000000-0000-4000-8000-000000000001',
    'owner'
)
on conflict (workspace_id, user_id) do update
set role = 'owner';

delete from public.workspaces
where workspace_id <> '00000000-0000-4000-8000-000000000002';

commit;
