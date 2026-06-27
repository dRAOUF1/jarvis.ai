# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## What is this repo

**jarvis.ai** — a non-technical user talks to a main agent about a project ("a sports coaching thing"),
the agent interviews them, compiles a `ProjectSpec` → `ArtifactBundle`, provisions a real **Hermes
agent** profile wired to the user's apps via **Composio** (MCP), scrapes initial memory, and hands
back a ready-to-chat agent. One user, many independent projects.

Pipeline: `user chat → [SHAPING] → ProjectSpec → [COMPILATION] → ArtifactBundle → [PROVISIONING] → ProfileHandle → [INGESTION] → MEMORY.md → READY → [RUNTIME] → SSE chat`

## Key docs (read before coding)

| File | What it is |
|---|---|
| `ARCHITECTURE.md` | **The bible.** Stack, frozen contracts, DB schema, API, session-key convention |
| `ARCHITECTURE_UML.md` | Mermaid diagrams — system architecture, sequence, class diagrams, state machine |
| `TEAM_PLAN.md` | Who owns what, order of work, integration checkpoints, per-folder kickoff prompts |
| `backend/CLAUDE.md` | Backend-local rules (FastAPI + Pydantic v2, frozen contracts, mock-first) |
| `frontend/CLAUDE.md` | Frontend-local rules (Next.js 14, types from `types.gen.ts`, mock-first) |
| `hermes/CLAUDE.md` | Hermes gateway rules (template profiles, MCP, version-pinning) |

## Architecture in 30 seconds

- **Control plane** (B1): `shaper.py` (slot-filling interview) → `compiler.py` (spec → bundle). Uses Anthropic Claude. AI fills free-text only; Jinja templates handle structure.
- **Worker plane** (B2): `AgentRuntime` ABC → `HermesRuntime` (POST to gateway) or `MockRuntime` (Anthropic + `memory` table). `RUNTIME_MODE` flips between them.
- **Connections** (C1): Composio OAuth → `Connection` (MCP URL + tool list). User-level, shared across projects.
- **Hermes wiring** (C2): `hermes_writer.py` stamps profile dirs from templates + MCP blocks. `ingestor.py` scrapes → summarizes → `MEMORY.md`.
- **Provisioning** (B2+C2): FSM state machine (compiling→connecting→provisioning→ingesting→ready). `ProfileProvisioner` ABC → `WarmPoolProvisioner` or `ModalProvisioner`.
- **Frontend** (F): Next.js 14 App Router. Dashboard, shaping chat (SSE), provisioning progress, project chat (SSE), connection toggles. Mock-first, one-line swap to real API.
- **DB**: Supabase Postgres. 6 tables (`users`, `projects`, `connections`, `project_tools`, `messages`, `memory`). Schema frozen in `ARCHITECTURE.md §5`.

## Monorepo layout

```
jarvis.ai/
├── ARCHITECTURE.md          # single source of truth
├── ARCHITECTURE_UML.md      # diagrams
├── TEAM_PLAN.md             # per-person work + integration plan
├── docker-compose.yml       # optional: local pg + backend
├── frontend/                # Next.js 14 (F)
├── backend/                 # FastAPI (B1+B2+C1+C2)
└── hermes/                  # profile templates + gateway scripts (C2)
```

See `ARCHITECTURE.md §3` for the full file tree with per-file ownership tags.

## Getting started

### Prerequisites

- **Python 3.12+** (backend)
- **Node.js 18+** (frontend)
- **Supabase** project (DB tables already created in production)
- `.env.local` at root with: `ANTHROPIC_API_KEY`, `SUPABASE_*`, `COMPOSIO_API_KEY`, `HERMES_*` URLs

### Backend setup

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # or: uv sync
uvicorn app.main:app --reload --port 8000   # dev server at http://localhost:8000
```

Key env vars: `RUNTIME_MODE=hermes|mock` (flip for demo insurance), `DEMO_USER_ID=demo-user`.

OpenAPI schema at `http://localhost:8000/openapi.json` is the type source for frontend `types.gen.ts`.

### Frontend setup

```bash
cd frontend
npm install
npm run dev   # Next.js dev server at http://localhost:3000
```

Generate TypeScript types from backend OpenAPI (run after any contract change):

```bash
npm run gen:types   # openapi-typescript http://localhost:8000/openapi.json -o lib/types.gen.ts
```

### Local Docker (optional)

```bash
docker compose up -d   # starts Postgres + backend (see docker-compose.yml)
```

### Scripts

- `backend/scripts/seed.py` — reset DB to known demo state (service-role key required)
- `backend/scripts/smoke_test.py` — headless hero-path test (must pass before any merge to `main` after H16)
- `backend/scripts/prewarm.sh` — ping Hermes gateways to keep warm

## Golden rules

1. **Contracts are frozen in `backend/app/contracts/`** — import them, never redefine. Changes are a `contract:` PR.
2. **Frontend types are GENERATED** from `/openapi.json` — never edit `lib/types.gen.ts` by hand.
3. **Mock-first at every seam** — `mockApi.ts`, `mock_connections.py`, `mock_bundle.py`, `MockRuntime`. Real impl swaps in behind the same interface.
4. **AI only in shaping, compilation (free-text), ingestion (summary)** — provisioning is 100% deterministic.
5. **Session-key format**: `X-Hermes-Session-Key: agent:{project_id}:user:{user_id}` — get this wrong and memory silently fails.
6. **Branches**: `f-frontend`, `b1-control`, `b2-runtime`, `c1-composio`, `c2-hermes`. PRs only, protect `main`.

## Contract models (the spine)

All handoff objects are Pydantic v2 models in `backend/app/contracts/models.py`:

| Model | Purpose |
|---|---|
| `ProjectSpec` | The shaped spec from the interview (name, goal, persona, tasks, tool_requirements, success_criteria) |
| `ArtifactBundle` | Compiled output (SOUL.md, USER.md, MEMORY.md, config.yaml, session/runtime keys) |
| `Connection` | Resolved Composio connection (id, app, mcp_url, available_tools, status) |
| `ProfileHandle` | Provisioned Hermes profile (gateway_url, session_key, runtime_key, status) |
| `Project` | DB-backed project row + embedded spec |
| `RuntimeEvent` | SSE union: delta / action / done / error |
| `ShapingEvent` | SSE union: delta / question / spec_update / proposal / done |
| `Msg` | Wire protocol message (role + content) |

Enums: `ProvisioningState` (7 values), `ConnectionStatus` (3 values).

## DB schema (6 tables, frozen)

`users` → `projects` (1:N), `users` → `connections` (1:N), `projects` → `project_tools` (1:N), `connections` → `project_tools` (1:N), `projects` → `messages` (1:N), `projects` → `memory` (1:N). See `ARCHITECTURE.md §5` for full SQL or `backend/app/db/migrations/schema.sql`.

## API endpoints (frozen)

| Method | Path | Owner | Purpose |
|---|---|---|---|
| POST | `/projects/shape` | B1 | SSE shaping stream |
| POST | `/projects` | B1+B2 | Create project (compile + provision) |
| GET | `/projects` | B2 | List projects |
| GET | `/projects/:id` | B2 | Get project |
| GET | `/projects/:id/status` | B2 | Provisioning state |
| GET | `/projects/:id/messages` | B2 | Message history |
| POST | `/projects/:id/chat` | B2 | SSE chat stream |
| GET | `/catalog` | C1 | App catalog |
| GET/POST | `/connections` | C1 | Manage connections |
| POST | `/meta` | B1 | Free-text need → ProjectSpec |

See `ARCHITECTURE.md §6` for full request/response shapes.

## Current status

- Supabase DB: **6 tables created and verified** in production (`https://xjvzysqygfpnnbegcsnn.supabase.co`)
- Contracts: **Pydantic models + TypeScript types generated** in `backend/app/contracts/models.py` and `frontend/lib/types.gen.ts`
- All implementation files: **empty stubs** — directory structure exists, no code yet
- Next milestone: implement mock-first (contracts + mocks working), then the hardcoded end-to-end Sports Coach + Strava demo
