-- jarvis.ai — Supabase database schema (FROZEN)
-- Source: ARCHITECTURE.md section 5
-- Apply: psql or Supabase SQL editor

create table if not exists users (
  id text primary key,
  name text,
  email text,
  created_at timestamptz default now()
);

create table if not exists projects (
  id uuid primary key default gen_random_uuid(),
  user_id text references users(id),
  name text not null,
  goal text,
  status text default 'draft',     -- draft|compiling|connecting|provisioning|ingesting|ready|failed
  failed_stage text,
  spec jsonb,                       -- the full ProjectSpec
  runtime_key text,                -- which warm gateway pair
  session_key text,                -- agent:{project_id}:user:{user_id}
  gateway_url text,
  avatar_seed text,
  created_at timestamptz default now()
);

create table if not exists connections (          -- user-level Composio connections (shared across projects)
  id uuid primary key default gen_random_uuid(),
  user_id text references users(id),
  app text not null,                -- strava | gmail | apple_health ...
  composio_account_id text,
  mcp_url text,
  status text default 'pending',    -- pending|connected|error
  scopes text[] default '{}',
  created_at timestamptz default now()
);

create table if not exists project_tools (        -- which connection + tool subset a project uses
  id uuid primary key default gen_random_uuid(),
  project_id uuid references projects(id),
  connection_id uuid references connections(id),
  allowed_tools text[] default '{}'
);

create table if not exists messages (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references projects(id),
  role text not null,               -- user | assistant
  content text not null,
  created_at timestamptz default now()
);

create table if not exists memory (               -- ingested context + mock-runtime fallback memory
  id uuid primary key default gen_random_uuid(),
  project_id uuid references projects(id),
  kind text,                        -- fact | weakness | preference | scraped
  content text,
  created_at timestamptz default now()
);

-- Indexes for common query patterns
create index if not exists idx_projects_user_id on projects(user_id);
create index if not exists idx_projects_status on projects(status);
create index if not exists idx_connections_user_id on connections(user_id);
create index if not exists idx_messages_project_id on messages(project_id);
create index if not exists idx_messages_created_at on messages(created_at);
create index if not exists idx_memory_project_id on memory(project_id);
create index if not exists idx_project_tools_project_id on project_tools(project_id);
create index if not exists idx_project_tools_connection_id on project_tools(connection_id);
