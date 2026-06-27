# jarvis.ai — Architecture & Build Bible (root `CLAUDE.md`)

> **Repo:** https://github.com/dRAOUF1/jarvis.ai
> **This file is the single source of truth.** Every Claude Code session in every folder reads this first.
> The picture is in `ARCHITECTURE_UML.md`. The per-person work is in `TEAM_PLAN.md`.

---

## 0. What we are building (read this even if you read nothing else)

A non-technical user opens the app and **talks to a main agent** about a project they want — say
"a sports coaching thing." Their first prompt is vague. The main agent **interviews them** (asks
what they want, what tasks, which apps to connect like Strava or Apple Health), then **compiles**
that conversation into a concrete set of files, **connects the chosen tools via Composio**,
**provisions a real Hermes profile** (the "sports coach") with memory and tools, **scrapes initial
context** from those tools, and hands the user a ready agent they can chat with — that remembers
them and acts for them. One user can create **many independent projects**, each its own agent with
its own goal and connections.

The whole system is a **pipeline of typed handoffs**:

```
user chat → [SHAPING] → ProjectSpec
          → [COMPILATION] → ArtifactBundle (SOUL.md, USER.md, config.yaml, tool list)
          → [CONNECTION] → Connection[] (authorized Composio accounts → MCP URLs + tools)
          → [PROVISIONING] → ProfileHandle (Hermes profile written, MCP registered, gateway warm)
          → [INGESTION] → seeded MEMORY.md
          → READY → [RUNTIME] → RuntimeEvent stream (chat + actions)
```

Each `→` is a **frozen contract**. That is what lets 5 people build in parallel.

**Two planes, kept strictly separate:**
- **Control plane** = the main/meta agent + the compiler. A backend-orchestrated Claude
  conversation with structured tool-calling. **Not a Hermes instance.** Dumb, deterministic, schema-constrained.
- **Worker plane** = the Hermes profiles. The actual project agents, with memory, MCP tools, power.

**Where AI is allowed and where it is forbidden:**
- AI is used in **shaping** (the interview), **compilation** (free-text fields only), and
  **ingestion** (one summarization call).
- AI is **forbidden** in **provisioning**. Given a finished `ArtifactBundle`, building the profile
  is 100% deterministic and reproducible. No model call decides whether a file gets written.

---

## 1. Stack (decided — do not re-litigate)

- **Frontend:** Next.js 14 (App Router) + TypeScript + Tailwind + **shadcn/ui** + lucide-react + framer-motion (light).
- **Backend:** **FastAPI (Python)**. Async. Pydantic v2 models everywhere.
- **DB:** Supabase Postgres (use the service-role key server-side).
- **Engine:** Hermes Agent (NousResearch/hermes-agent), **version-pinned**, run as gateway processes, OpenAI-compatible REST. Underlying model = Claude Sonnet 4.6 (set in `config.yaml`).
- **Tools/integrations:** **Composio** (one account, OAuth in test mode), exposed to Hermes as MCP servers.
- **Fallback engine:** direct Anthropic call + a Postgres `memory` table (the `mock` runtime).
- **Deploy:** Vercel (frontend) · one always-on VPS / warm Modal app (FastAPI + Hermes gateways) · Cloudflare Tunnel/ngrok for HTTPS · Supabase (DB).

---

## 2. THE UNIFICATION MECHANISM (how 5 separate builds become one app)

Three rules. Break any one of them and integration becomes merge hell.

### 2.1 Contracts are the spine — Pydantic is the source of truth
All handoff objects live in **`backend/app/contracts/`** as Pydantic v2 models. **Nobody redefines
these anywhere.** A contract changes *there first*, in a PR titled `contract:`, and is announced in
the team channel. Never edit a contract locally inside your own folder.

### 2.2 Frontend types are GENERATED, never hand-written
FastAPI auto-emits an OpenAPI schema at `/openapi.json`. The frontend runs:

```bash
# from /frontend
npm run gen:types     # = openapi-typescript http://localhost:8000/openapi.json -o lib/types.gen.ts
```

→ producing `frontend/lib/types.gen.ts`. The frontend imports types **only** from there. This means
the Python contracts and the TypeScript types **can never drift** — they come from the same source.
Re-run `gen:types` whenever a contract changes.

### 2.3 Mock-first at every seam — nobody waits for the team upstream
Every team builds against a mock of the team before it, behind the real interface:
- **F** builds against `lib/mockApi.ts` until the backend is live (one-line swap to the real client).
- **B1** (compiler) runs against `mocks/mock_connections.py`.
- **C2** (wiring) runs against `mocks/mock_bundle.py` (a hand-written sample `ArtifactBundle`).
- **B2** (runtime) ships with `MockRuntime` on hour one; `RUNTIME_MODE=mock` works before Hermes does.

"Connecting at the end" then means **swapping a mock for a real impl behind an interface that already
matched** — a one-line change, not an integration.

---

## 3. Monorepo layout (frozen)

```
jarvis.ai/
├── CLAUDE.md                      # this file (root rules; every Claude Code reads it)
├── ARCHITECTURE_UML.md            # the diagrams
├── TEAM_PLAN.md                   # per-person work + integration plan
├── docker-compose.yml             # optional: pg + backend for local
│
├── frontend/                      # ── F owns everything here ──
│   ├── CLAUDE.md                  # F's local rules
│   ├── app/
│   │   ├── page.tsx               # Dashboard: grid of project cards
│   │   ├── create/page.tsx        # Shaping chat (the main agent)
│   │   ├── project/[id]/page.tsx  # Project agent chat + side panel
│   │   ├── project/[id]/provisioning/page.tsx   # progress view (state machine)
│   │   └── project/[id]/connections/page.tsx    # connect apps / OAuth toggles
│   ├── components/
│   │   ├── ShapingChat.tsx  ProjectCard.tsx  ProjectGrid.tsx
│   │   ├── ProvisioningProgress.tsx  ConnectionToggle.tsx
│   │   ├── ChatThread.tsx  Composer.tsx  SidePanel.tsx  StatusDot.tsx
│   ├── lib/
│   │   ├── api.ts                 # typed API client (real)
│   │   ├── mockApi.ts             # mock (swap target)
│   │   ├── types.gen.ts           # GENERATED from OpenAPI — DO NOT EDIT
│   │   ├── useAgentStream.ts      # SSE hook for /chat
│   │   ├── useShapingStream.ts    # SSE hook for /shape
│   │   └── design/tokens.css
│   ├── package.json
│   └── ...
│
├── backend/                       # ── Python / FastAPI ──
│   ├── CLAUDE.md                  # backend-wide rules
│   ├── app/
│   │   ├── main.py                # FastAPI app + router registration      [B2]
│   │   ├── config.py              # settings / env (pydantic-settings)     [B2]
│   │   ├── deps.py                # DI: db client, runtime, provisioner    [B2]
│   │   │
│   │   ├── contracts/             # ★ SOURCE OF TRUTH — whole team freezes together
│   │   │   ├── __init__.py
│   │   │   ├── spec.py            # ProjectSpec, TaskItem, ToolRequirement
│   │   │   ├── bundle.py          # ArtifactBundle
│   │   │   ├── connection.py      # Connection, ConnectionStatus, AppCatalogItem
│   │   │   ├── profile.py         # ProfileHandle, ProvisioningState
│   │   │   ├── runtime.py         # RuntimeEvent, Msg
│   │   │   ├── shaping.py         # ShapingEvent
│   │   │   └── api.py             # request/response wrappers per endpoint
│   │   │
│   │   ├── routers/               # THIN handlers, partitioned by owner
│   │   │   ├── projects.py        # /projects (create), /projects/:id        [B2 scaffold; B1 create-logic]
│   │   │   ├── shaping.py         # /projects/shape (SSE)                     [B1]
│   │   │   ├── chat.py            # /projects/:id/chat (SSE)                  [B2]
│   │   │   ├── provisioning.py    # /projects/:id/status                      [B2]
│   │   │   ├── connections.py     # /connections, /catalog                    [C1]
│   │   │   └── meta.py            # /meta (free-text need -> spec)            [B1]
│   │   │
│   │   ├── control/               # ── B1: control plane ──
│   │   │   ├── shaper.py          # the slot-filling interview
│   │   │   ├── compiler.py        # ProjectSpec -> ArtifactBundle
│   │   │   ├── llm.py             # Anthropic client wrapper (shared)
│   │   │   ├── catalog.py         # app catalog data (shared read w/ C1)
│   │   │   └── templates/
│   │   │       ├── soul.md.j2     # deterministic SOUL skeleton (AI fills slots)
│   │   │       └── config.yaml.j2 # deterministic Hermes config skeleton
│   │   │
│   │   ├── runtime/               # ── B2: worker plane ──
│   │   │   ├── base.py            # AgentRuntime ABC  (== contract §1.8)
│   │   │   ├── hermes_runtime.py  # HermesRuntime
│   │   │   ├── mock_runtime.py    # MockRuntime (Anthropic + memory table)
│   │   │   └── factory.py         # get_runtime() reads RUNTIME_MODE
│   │   │
│   │   ├── provisioning/          # ── B2 + C2 ──
│   │   │   ├── provisioner.py     # ProfileProvisioner ABC + WarmPoolProvisioner   [B2]
│   │   │   ├── state_machine.py   # the provisioning FSM + status persistence       [B2]
│   │   │   ├── hermes_writer.py   # stamp profile dir, write config.yaml + MCP      [C2]
│   │   │   └── gateway.py         # warm-pool / gateway lifecycle                    [B2+C2]
│   │   │
│   │   ├── connections/           # ── C1: Composio ──
│   │   │   ├── composio_client.py # Composio SDK/API wrapper
│   │   │   ├── oauth.py           # connect / callback / status
│   │   │   └── mcp_exposer.py     # connection -> MCP URL + scoped tool list
│   │   │
│   │   ├── ingestion/             # ── C2: scrape -> memory ──
│   │   │   ├── ingestor.py        # orchestrates: per-app scrape -> summarize -> MEMORY.md
│   │   │   ├── summarizer.py      # ONE Claude call -> structured memory entries
│   │   │   └── jobs/
│   │   │       ├── strava.py      # bounded read-only calls for one app
│   │   │       ├── gmail.py
│   │   │       └── apple_health.py
│   │   │
│   │   ├── db/                    # ── B2 ──
│   │   │   ├── client.py          # supabase client (service role)
│   │   │   ├── queries.py         # typed query helpers
│   │   │   └── migrations/
│   │   │       └── schema.sql     # FROZEN schema (§5)
│   │   │
│   │   └── mocks/                 # mock impls for every seam
│   │       ├── mock_connections.py
│   │       ├── mock_bundle.py
│   │       └── mock_runtime_data.py
│   │
│   ├── scripts/
│   │   ├── seed.py                # reset demo to known state                  [E-role / shared]
│   │   ├── smoke_test.py          # full hero-path headless gate
│   │   └── prewarm.sh             # ping gateways to keep warm
│   ├── pyproject.toml
│   └── requirements.txt
│
└── hermes/                        # ── C2 owns ──
    ├── CLAUDE.md
    ├── profiles/
    │   └── _template/             # template profile stamped per project
    │       ├── SOUL.md  USER.md  MEMORY.md  config.yaml
    ├── mcp/
    │   └── composio_snippet.yaml  # MCP block shape filled from Connection objects
    └── scripts/
        ├── create_profile.sh  run_gateway.sh  prewarm.sh
```

---

## 4. Environment variables (`.env` contract — names frozen)

```
# Anthropic
ANTHROPIC_API_KEY=

# Supabase
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# Engine selection
RUNTIME_MODE=hermes              # hermes | mock  (flip to mock if Hermes breaks)
PROVISIONER_MODE=warmpool        # warmpool | modal

# Composio
COMPOSIO_API_KEY=

# Warm Hermes gateways (one pair per warm slot; A/B are the two demo agents, P1/P2 the spare pool)
HERMES_A_URL=                    # https://<tunnel>/v1
HERMES_A_KEY=
HERMES_B_URL=
HERMES_B_KEY=
HERMES_POOL_URLS=                # comma-separated spare gateway URLs for new projects
HERMES_POOL_KEYS=

# Demo
DEMO_USER_ID=demo-user           # single hardcoded user for the hackathon
```

---

## 5. Database schema (FROZEN — `backend/app/db/migrations/schema.sql`)

> One **project** == one agent == one Hermes profile.

```sql
create table users (
  id text primary key,
  name text, email text,
  created_at timestamptz default now()
);

create table projects (
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

create table connections (          -- user-level Composio connections (shared across projects)
  id uuid primary key default gen_random_uuid(),
  user_id text references users(id),
  app text not null,                -- strava | gmail | apple_health ...
  composio_account_id text,
  mcp_url text,
  status text default 'pending',    -- pending|connected|error
  scopes text[] default '{}',
  created_at timestamptz default now()
);

create table project_tools (        -- which connection + tool subset a project uses
  id uuid primary key default gen_random_uuid(),
  project_id uuid references projects(id),
  connection_id uuid references connections(id),
  allowed_tools text[] default '{}'
);

create table messages (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references projects(id),
  role text not null,               -- user | assistant
  content text not null,
  created_at timestamptz default now()
);

create table memory (               -- ingested context + mock-runtime fallback memory
  id uuid primary key default gen_random_uuid(),
  project_id uuid references projects(id),
  kind text,                        -- fact | weakness | preference | scraped
  content text,
  created_at timestamptz default now()
);
```

---

## 6. REST + SSE API contract (FROZEN)

| Method | Path | Body | Returns | Owner |
|---|---|---|---|---|
| POST | `/projects/shape` | `{project_id?, message}` | **SSE** `ShapingEvent` stream | B1 |
| POST | `/projects` | `{spec: ProjectSpec, connection_ids: str[]}` | `{project}` (kicks off provisioning) | B2 route, B1 compile |
| GET | `/projects` | — | `{projects: Project[]}` | B2 |
| GET | `/projects/:id` | — | `{project}` | B2 |
| GET | `/projects/:id/status` | — | `{status: ProvisioningState, failed_stage?}` | B2 |
| GET | `/projects/:id/messages` | — | `{messages: Message[]}` | B2 |
| POST | `/projects/:id/chat` | `{message}` | **SSE** `RuntimeEvent` stream | B2 |
| GET | `/catalog` | — | `{apps: AppCatalogItem[]}` | C1 |
| GET | `/connections` | — | `{connections: Connection[]}` | C1 |
| POST | `/connections` | `{app}` | `{connection, redirect_url?}` | C1 |
| GET | `/connections/callback` | (oauth) | redirect | C1 |
| POST | `/meta` | `{need}` | `{spec: ProjectSpec}` | B1 |

**SSE format (both streams):** each event is a line `data: {json}\n\n`. The JSON is a tagged union
(`{"type": "delta", "text": "..."}` etc.) matching `contracts/runtime.py` / `contracts/shaping.py`.

---

## 7. Session-key convention (FROZEN — this is what makes memory persist)

- Header **`X-Hermes-Session-Key`** = `agent:{project_id}:user:{user_id}` → stable across sessions →
  this is what makes the agent remember the user. Store it on the `projects` row.
- Header **`X-Hermes-Session-Id`** = a fresh uuid per conversation thread (the transcript).
- **Get this wrong and memory silently fails.** Test it at every checkpoint.

---

## 8. The two key interfaces (FROZEN — the insurance policies)

```python
# contracts/runtime.py
from typing import AsyncIterable, Literal, Union
from pydantic import BaseModel

class Msg(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

class Delta(BaseModel):  type: Literal["delta"] = "delta";  text: str
class Action(BaseModel): type: Literal["action"] = "action"; label: str; detail: str | None = None
class Done(BaseModel):   type: Literal["done"] = "done"
class Err(BaseModel):    type: Literal["error"] = "error"; message: str
RuntimeEvent = Union[Delta, Action, Done, Err]

# runtime/base.py
from abc import ABC, abstractmethod
class AgentRuntime(ABC):
    @abstractmethod
    def chat(self, *, project_id: str, session_key: str, session_id: str,
             messages: list[Msg]) -> AsyncIterable[RuntimeEvent]: ...

# provisioning/provisioner.py
class ProfileProvisioner(ABC):
    @abstractmethod
    async def provision(self, bundle: "ArtifactBundle",
                        connections: list["Connection"]) -> "ProfileHandle": ...
    @abstractmethod
    async def status(self, project_id: str) -> "ProvisioningState": ...
```

`get_runtime()` returns Hermes or Mock by `RUNTIME_MODE`. The frontend never knows which is running.
`provision()` runs the state machine in §5 of `ARCHITECTURE_UML.md`. Behind `PROVISIONER_MODE` so we
can swap WarmPool → Modal later with zero changes elsewhere.

---

## 9. Git & working conventions (every Claude Code obeys)

- **Branch per team:** `f-frontend`, `b1-control`, `b2-runtime`, `c1-composio`, `c2-hermes`.
- **Protect `main`.** PRs only. Small PRs. Never push broken code to `main`.
- **Contract changes** are their own PR (`contract:` prefix) and announced before merge.
- Each folder has a local `CLAUDE.md`; your Claude Code session works **inside your folder** so
  contexts don't collide. The only shared edit surface is `backend/app/contracts/`.
- After H-checkpoint with a real backend, `backend/scripts/smoke_test.py` must pass before any merge to `main`.

### First-time repo setup (run once, by whoever bootstraps)
```bash
git clone https://github.com/dRAOUF1/jarvis.ai.git
cd jarvis.ai
# add these three files at the root, plus folder skeletons + CLAUDE.md per folder
git add CLAUDE.md ARCHITECTURE_UML.md TEAM_PLAN.md
git commit -m "docs: architecture, UML, team plan"
git push origin main
# protect main in GitHub settings, then everyone branches:
git checkout -b f-frontend     # (etc. per person)
```

---

## 10. The three things that win or lose this build

1. **Freeze the contracts (§5–§8) in the first 45 minutes** — then everyone codes against frozen types.
2. **Prove ONE hardcoded project end-to-end before building shaping on top** — a hand-written
   `ArtifactBundle` + one Composio connection → provisioned profile → ingestion → chat with working
   memory. This is the make-or-break hour (see `TEAM_PLAN.md` H2–H6).
3. **Keep `RUNTIME_MODE=mock` flippable in under a minute** — your demo-morning insurance, plus a
   **backup video** recorded by H30.
