# jarvis.ai — Team Build Plan

> Read `ARCHITECTURE.md` first (the what), then `ARCHITECTURE_UML.md` (the picture). This is the **who
> does what, in which file, in what order, and how it all sticks together**.
>
> **5 people:** F (frontend) · B1 + B2 (backend) · C1 + C2 (MCP/Composio).

---

## 0. The first 45 minutes — EVERYONE, together (do not skip)

Nothing parallelizes until this is done. Sit together and:

1. **Create the repo skeleton** — folders from `ARCHITECTURE.md §3`, empty files, a `CLAUDE.md` in
   each folder (content below), push to `main`. One person drives; the rest watch and agree.
2. **Write the contracts together** — fill in `backend/app/contracts/*.py` (`spec.py`, `bundle.py`,
   `connection.py`, `profile.py`, `runtime.py`, `shaping.py`). Use the class diagram in
   `ARCHITECTURE_UML.md §3` and the interfaces in `ARCHITECTURE.md §8`. **These are frozen after this
   session.** Any later change is a `contract:` PR announced to all 5.
3. **Write `schema.sql`** (`ARCHITECTURE.md §5`) and run it on Supabase.
4. **Write the mocks** — `mocks/mock_connections.py`, `mocks/mock_bundle.py`, `mocks/mock_runtime_data.py`,
   and `frontend/lib/mockApi.ts`. These let everyone start immediately.
5. **Agree the demo project** for the hardcoded end-to-end test: a **Sports Coach** that connects
   **Strava** (read activities) and drills/encourages the user. Write a sample `ProjectSpec` and a
   sample `ArtifactBundle` as the mock fixtures.
6. Everyone branches: `f-frontend`, `b1-control`, `b2-runtime`, `c1-composio`, `c2-hermes`.

Once contracts + mocks exist, the five workstreams below run in parallel.

---

## 1. How to launch your Claude Code (each person)

```bash
cd jarvis.ai
git checkout <your-branch>
cd <your-folder>     # frontend/ or backend/
claude               # start Claude Code INSIDE your folder so contexts don't collide
```

Your folder's `CLAUDE.md` + the root `ARCHITECTURE.md` give Claude Code everything it needs. Each
person's **kickoff prompt** is in their section below — paste it as your first message to Claude Code.

> **Golden rule for every Claude Code session:** "Import contracts from `app/contracts` (or
> `lib/types.gen.ts`). Never redefine a contract type. Build against the mock until the real
> dependency is green. Keep handlers thin. Small commits."

---

## 2. F — Frontend (1 person)

**Folder:** `frontend/` · **Branch:** `f-frontend`
**You own the entire non-tech user experience.** You consume REST + two SSE streams. You build
against `lib/mockApi.ts` until backends land, then swap one line.

### Files you own
| File | What it does |
|---|---|
| `app/page.tsx` | Dashboard — grid of `ProjectCard`s from `GET /projects`, "+ New project" card |
| `app/create/page.tsx` | **Shaping chat** with the main agent (SSE `/projects/shape`) → on proposal, show spec + app picker → `POST /projects` |
| `app/project/[id]/provisioning/page.tsx` | **Progress view** — polls `GET /projects/:id/status`, renders the state machine (compiling→connecting→provisioning→ingesting→ready) |
| `app/project/[id]/connections/page.tsx` | Connect-apps screen — toggles from `GET /catalog`, `POST /connections`, OAuth redirect |
| `app/project/[id]/page.tsx` | Project agent chat (SSE `/projects/:id/chat`) + right-hand **SidePanel** (memory chips + recent actions) |
| `components/*` | `ShapingChat`, `ProjectCard`, `ProjectGrid`, `ProvisioningProgress`, `ConnectionToggle`, `ChatThread`, `Composer`, `SidePanel`, `StatusDot` |
| `lib/api.ts` | typed API client (real) |
| `lib/mockApi.ts` | mock client (your starting point; one-line swap) |
| `lib/useShapingStream.ts` | SSE hook → `{messages, streamingText, partialSpec, proposal, send()}` |
| `lib/useAgentStream.ts` | SSE hook → `{messages, streamingText, actions, send()}` |
| `lib/design/tokens.css` | dark theme, indigo accent #6D5EF7, Inter, 16px radius |

**Never edit** `lib/types.gen.ts` (generated). Run `npm run gen:types` after any contract change.

### Order of work
1. Scaffold + tokens + shadcn primitives. 2. Dashboard against mock. 3. Shaping chat + the two SSE
hooks against mock streams. 4. Provisioning progress view. 5. Connections screen. 6. Project chat +
side panel. 7. Swap `mockApi`→`api` per endpoint as each backend route lands. 8. Polish to "beautiful"
at 1280px (projector resolution).

### Claude Code kickoff prompt
> You are building the Next.js 14 App Router frontend for "jarvis.ai" in `frontend/`. Read the root
> `ARCHITECTURE.md` and `frontend/CLAUDE.md`. Use Tailwind + shadcn/ui + the tokens in
> `lib/design/tokens.css` (dark, indigo #6D5EF7, Inter, 16px radius, calm/premium, Linear-meets-Raycast).
> Build the screens and components listed in `TEAM_PLAN.md §2`. Import all types from `lib/types.gen.ts`.
> Read from `lib/mockApi.ts` for now; make swapping to `lib/api.ts` a one-line change. Implement
> `useShapingStream` and `useAgentStream` to parse `data: {json}` SSE lines into the union events from
> the contracts. Keep components small and accessible; animate only on enter/hover.

### Definition of done
Full click-path works against mock: shape a project → see it provision → connect an app → chat with
side panel updating live. Swapping to the real API is one line per endpoint. Looks demo-ready at 1280px.

---

## 3. B1 — Backend, Control Plane / the "brain" (1 person)

**Folder:** `backend/app/control/` + `routers/shaping.py`, `routers/meta.py`, create-logic in `routers/projects.py`
**Branch:** `b1-control`
**You own the main agent and the compiler** — turning a dumb prompt into a complete `ProjectSpec`,
then a `ProjectSpec` into a valid `ArtifactBundle`. You code against `mocks/mock_connections.py` and
the app catalog.

### Files you own
| File | What it does |
|---|---|
| `control/shaper.py` | The slot-filling interview. Multi-turn Claude conversation with structured tool-calling that progressively fills a `ProjectSpec`; recommends apps from `catalog.py`; calls `finalize` when required slots are full. Streams `ShapingEvent`s. |
| `control/compiler.py` | `ProjectSpec → ArtifactBundle`. **AI fills only free-text fields** (SOUL persona body, task descriptions). **Templates produce structure** (`config.yaml`, MCP blocks, `allowed_tools`). Validate every AI output against the Pydantic schema; hardcoded fallback template if validation fails. |
| `control/llm.py` | Anthropic client wrapper (claude-sonnet-4-6), shared with ingestion's summarizer. |
| `control/catalog.py` | The app catalog data the shaper recommends from (strava, gmail, apple_health, ...). Read-shared with C1. |
| `control/templates/soul.md.j2` | Deterministic SOUL skeleton with slots the AI fills. |
| `control/templates/config.yaml.j2` | Deterministic Hermes `config.yaml` skeleton (model, API server, MCP block placeholder). |
| `routers/shaping.py` | `POST /projects/shape` → SSE stream of `ShapingEvent` from `shaper.py`. |
| `routers/meta.py` | `POST /meta` → one Claude call, free-text need → `ProjectSpec` (defensive JSON parse, fallback template). |
| create-logic in `routers/projects.py` | the body of `POST /projects`: call `compiler.compile(spec)`, then hand the bundle to B2's provisioner. (B2 owns the file scaffold; you fill the create handler.) |

### The hard part: deterministic compilation
Push **all** AI to the edges. The compiler's job is mostly **templating**. The MCP blocks in
`config.yaml` are stamped from the `ToolRequirement[]` + resolved `Connection[]` — **no AI decides
file structure**. If the AI's free-text field fails schema validation, drop to the fallback template
and keep going. The provisioner downstream must receive a 100%-valid bundle every time.

### Claude Code kickoff prompt
> You are building the control plane for "jarvis.ai" in `backend/app/control/` (FastAPI, Pydantic v2,
> async). Read root `ARCHITECTURE.md` + `backend/CLAUDE.md`. Import contracts from `app.contracts`;
> never redefine them. Build `shaper.py` (a slot-filling interview using Anthropic tool-calling that
> fills a `ProjectSpec` and streams `ShapingEvent`s), `compiler.py` (`ProjectSpec → ArtifactBundle`,
> AI only for free-text fields, Jinja templates for structure, schema-validate every output with a
> hardcoded fallback), `llm.py`, `catalog.py`, the two `templates/*.j2`, and the SSE route in
> `routers/shaping.py` + `routers/meta.py`. Use `mocks/mock_connections.py` for connection data.
> Give me curl commands to test each.

### Definition of done
`POST /meta {need}` returns a valid `ProjectSpec` 5/5 times. `/projects/shape` runs a coherent
interview and emits a `proposal`. `compiler.compile(spec)` returns a schema-valid `ArtifactBundle`
whose `config.yaml` parses as YAML — every time.

---

## 4. B2 — Backend, Runtime / Infra plane + the plumbing everyone plugs into (1 person)

**Folder:** `backend/app/runtime/`, `backend/app/provisioning/` (the B2 files), `backend/app/db/`,
`main.py`, `config.py`, `deps.py`, the **router scaffold**, `chat.py`, `provisioning.py`, `projects.py` scaffold
**Branch:** `b2-runtime`
**You own the spine of the backend.** You unblock B1 and C1 by giving them the FastAPI app, the DB
client, and the router files to drop handlers into. You ship `MockRuntime` on hour one so the whole
team has a working engine before Hermes exists.

### Files you own
| File | What it does |
|---|---|
| `main.py` | FastAPI app, CORS, registers all routers, exposes `/openapi.json` (the type source for F). |
| `config.py` | `pydantic-settings` reading the `.env` contract. |
| `deps.py` | DI providers: db client, `get_runtime()`, `get_provisioner()`. |
| `db/client.py`, `db/queries.py` | Supabase service-role client + typed query helpers used by every router. |
| `db/migrations/schema.sql` | the frozen schema (you run it). |
| `runtime/base.py` | `AgentRuntime` ABC + `RuntimeEvent` (matches contract §8). |
| `runtime/hermes_runtime.py` | POST to `${gateway}/chat/completions` with bearer + session headers; parse SSE; emit `delta`/`action`/`done`. |
| `runtime/mock_runtime.py` | Anthropic SDK directly + read/write the `memory` table to fake persistence. Same interface. |
| `runtime/factory.py` | `get_runtime()` by `RUNTIME_MODE`. |
| `provisioning/provisioner.py` | `ProfileProvisioner` ABC + `WarmPoolProvisioner` (assign a warm gateway from the pool, bind the new profile, return `ProfileHandle`). |
| `provisioning/state_machine.py` | the FSM: drives compiling→connecting→provisioning→ingesting→ready, persists `status`/`failed_stage` on the `projects` row. Calls C2's `hermes_writer` + `ingestor` and C1's connection resolution at the right steps. |
| `provisioning/gateway.py` | warm-pool registry + health pings (co-owned with C2). |
| `routers/projects.py` | scaffold for `/projects` GET/POST/`:id` (B1 fills create-logic). |
| `routers/chat.py` | `POST /projects/:id/chat` → SSE `ReadableStream` forwarding `RuntimeEvent`s; persists messages. |
| `routers/provisioning.py` | `GET /projects/:id/status`. |

### The most important thing you do
The **provisioning state machine** is the orchestrator that ties C1, C2, and B1's output together.
It receives the `ArtifactBundle` (from B1) + `Connection[]` (from C1), then calls — in order —
C2's `hermes_writer.write()`, gateway warm, C2's `ingestor.ingest()`, and flips status to `ready`.
You define the seams; C1/C2 implement what plugs in. Keep them behind the ABCs so you can run the
whole machine with mocks before their real code lands.

### Claude Code kickoff prompt
> You are building the runtime/infra backbone for "jarvis.ai" in `backend/app/` (FastAPI, Pydantic v2,
> async). Read root `ARCHITECTURE.md` + `backend/CLAUDE.md`. Build `main.py` (register routers, expose
> OpenAPI), `config.py`, `deps.py`, the Supabase `db/` client + queries, the `runtime/` package
> (`AgentRuntime` ABC, `HermesRuntime`, `MockRuntime` using Anthropic + the `memory` table, `factory`),
> the `provisioning/` package (`ProfileProvisioner` ABC, `WarmPoolProvisioner`, and the
> `state_machine` that walks the FSM in ARCHITECTURE_UML §5 and persists status), and the routers
> `projects.py` (scaffold), `chat.py` (SSE), `provisioning.py`. Use the frozen session-key convention
> from `ARCHITECTURE.md §7`. Make `RUNTIME_MODE=mock` fully work before Hermes exists. Give me curl
> commands, including `curl -N` for the SSE chat endpoint.

### Definition of done
`RUNTIME_MODE=mock` streams chat end-to-end and "remembers" via the `memory` table. The state machine
runs to `ready` against mock writer/ingestor. Flipping `RUNTIME_MODE` needs no frontend change.

---

## 5. C1 — Composio platform (1 person)

**Folder:** `backend/app/connections/` + `routers/connections.py`
**Branch:** `c1-composio`
**You own "the user can connect their real apps."** You make a `Connection` **authorized and
exposed** (an MCP URL + scoped tool list). You hand that object to C2 and to the state machine.

### Files you own
| File | What it does |
|---|---|
| `connections/composio_client.py` | Wrapper over Composio: list available apps, initiate connection, check status, fetch the per-account MCP URL + available tools. |
| `connections/oauth.py` | `connect(app)` → redirect URL; `callback` → mark connection `connected`, store `composio_account_id` + `mcp_url`. |
| `connections/mcp_exposer.py` | Given a connected account, produce `{mcp_url, available_tools}`; apply scope/tool subsetting. |
| `routers/connections.py` | `GET /catalog`, `GET /connections`, `POST /connections`, `GET /connections/callback`. |
| `control/catalog.py` | (co-own with B1) the catalog data: app id, display name, "what it does", icon, default tool subset. |

### Key decisions
- **Connections are user-level**, not project-level. Authorize Strava once; many projects reference
  it with their own `allowed_tools` subset (`project_tools` table).
- **Test-mode OAuth** — add the team account as a test user; restricted scopes work without verification.
- **Get ONE app working end-to-end first** (Strava for the sports demo). Add a second only after.
- The output object is the frozen `Connection` contract — that's the only thing C2 and B2 see.

### Claude Code kickoff prompt
> You are building the Composio integration layer for "jarvis.ai" in `backend/app/connections/`
> (FastAPI, async). Read root `ARCHITECTURE.md` + `backend/CLAUDE.md`. Import contracts from
> `app.contracts`. Build `composio_client.py`, `oauth.py`, `mcp_exposer.py`, the `routers/connections.py`
> endpoints, and the app catalog data. The output of a successful connect is a `Connection` object with
> `status=connected`, `mcp_url`, and `available_tools`. Connections are user-level and reusable across
> projects. Use Composio test-mode OAuth. Start with Strava only. Give me a curl + browser walkthrough
> to authorize one app and confirm the MCP URL + tools come back.

### Definition of done
A user can connect Strava via OAuth; `GET /connections` returns it `connected` with an `mcp_url` and a
real `available_tools` list. `GET /catalog` lists the apps the shaper can recommend.

---

## 6. C2 — Hermes wiring + Ingestion (1 person)

**Folder:** `backend/app/provisioning/hermes_writer.py`, `backend/app/ingestion/`, the `hermes/` folder
**Branch:** `c2-hermes`
**You own the deterministic half + the scrape.** You turn a `Connection` + `ArtifactBundle` into a
**real, running, tool-using Hermes profile**, then **scrape initial memory** into it. You code against
`mocks/mock_bundle.py` (a hand-written sample bundle) until B1's compiler is live.

### Files you own
| File | What it does |
|---|---|
| `hermes/profiles/_template/*` | The template profile dir (SOUL.md, USER.md, MEMORY.md, config.yaml) stamped per project. |
| `hermes/mcp/composio_snippet.yaml` | The MCP block shape filled from `Connection` objects. |
| `hermes/scripts/create_profile.sh`, `run_gateway.sh`, `prewarm.sh` | Stand up + warm a gateway from a profile dir. |
| `provisioning/hermes_writer.py` | `write(bundle, connections)`: stamp the profile dir, write `config.yaml` with MCP blocks built from the connections' `mcp_url` + `allowed_tools`, register MCP, `/reload-mcp`. **Handle the gotchas:** tool calls run on the gateway host, `npx`/MCP must be on the gateway's PATH, verify with an MCP test call; if 0 tools appear the handshake failed. |
| `ingestion/ingestor.py` | `ingest(project, connections)`: run **bounded, read-only** scrape jobs per connected app, pass results through the summarizer, write entries to `MEMORY.md` (Hermes mode) and the `memory` table (mock mode). **Time-boxed. Never open-ended.** |
| `ingestion/summarizer.py` | ONE Claude call → structured memory entries (`fact`/`preference`/`scraped`). |
| `ingestion/jobs/strava.py`, `gmail.py`, `apple_health.py` | Per-app fixed list of read-only calls. |

### Key decisions
- **Ingestion scope creep is the #1 risk in your lane.** Each `jobs/*.py` is a **fixed, small** set
  of read-only calls. One summarization call. A hard time box. Resist "just one more endpoint."
- The MCP block is built **deterministically** from the `Connection` — no AI. Same input → same config.
- Coordinate the warm-pool with B2: B2 owns the pool registry; you own what gets written into a slot.

### Claude Code kickoff prompt
> You are building the Hermes wiring + ingestion for "jarvis.ai" in `backend/app/provisioning/hermes_writer.py`,
> `backend/app/ingestion/`, and the `hermes/` folder. Read root `ARCHITECTURE.md` + `backend/CLAUDE.md` +
> `hermes/CLAUDE.md`. Import contracts from `app.contracts`. Build the template profile, `hermes_writer.py`
> (stamp profile dir + write config.yaml with Composio MCP blocks from `Connection` objects, register MCP,
> reload, verify tools appear), the bash scripts, and the `ingestion/` package (a bounded per-app
> read-only scrape → one Claude summarization call → MEMORY.md + `memory` table). Use `mocks/mock_bundle.py`
> until the real compiler is live. Strava first. Everything here is deterministic except the one
> summarization call. Give me commands to stamp a profile, warm a gateway, and confirm a tool call works.

### Definition of done
Given the sample bundle + a Strava `Connection`, you produce a running gateway whose `mcp test` returns
real Strava data, and `ingest()` writes meaningful memory entries the agent recalls in chat.

---

## 7. The integration plan — how 5 builds become 1 app

You integrate **upward along the pipeline at checkpoints**, not all at once at the end. Hours are
relative to start.

| Hour | Gate | Who | What must be true |
|---|---|---|---|
| **H0–H1** | Contracts frozen | ALL | `contracts/*`, `schema.sql`, mocks, sample spec+bundle on `main`. Branches cut. |
| **H1–H6** | **The make-or-break hour: ONE hardcoded project end-to-end** | B2+C1+C2 | Hand-written `ArtifactBundle` + one real Strava `Connection` → `WarmPoolProvisioner` stamps a profile (C2) → gateway warm → `ingest()` seeds memory (C2) → `HermesRuntime` chat streams with working memory. **No shaping, no UI yet. Nothing builds on top until this is green.** |
| **H1–H6** | (parallel) F + B1 on mocks | F, B1 | F: dashboard + shaping chat against mock streams. B1: `/meta` + shaper + compiler against mock connections. |
| **H6–H12** | Shaping → Spec → Bundle live | B1+F | F's shaping chat hits real `/projects/shape`; B1's compiler produces a valid bundle from a real spec. |
| **H12–H16** | Bundle → Connections → Provision live | B1+C1+B2 | `POST /projects` runs the real state machine: compile → resolve real `Connection`s (C1) → provision (B2/C2). F's provisioning progress view shows real status. |
| **H16–H20** | Ingestion + live chat in the UI | C2+B2+F | A project created from scratch in the UI scrapes real memory and is chattable with the side panel updating live. |
| **H20–H24** | Second app + second project type + polish | C1+C2+F | Add a 2nd Composio app; create a different project (not just sports) to prove genericity; UI polish pass. |
| **H24–H28** | Harden ONE known-good demo path; freeze features | ALL | `smoke_test.py` green 5× in a row. |
| **H30** | **Backup video** of the full hero path | F+B1 lead | Recorded and tested. |
| **H32–H35** | Rehearse demo ≥5×; deck + Q&A | ALL | Whole team can run it cold. |

### The smoke test that gates merges after H16
`backend/scripts/smoke_test.py` runs the hero path headless: create a project from a fixed spec →
assert it reaches `ready` → chat → assert an `action` event + a memory recall. Must pass before any
merge to `main`.

### Demo-morning insurance
- Flip `RUNTIME_MODE=mock` (works in <60s) if Hermes misbehaves — frontend and demo identical.
- Flip `PROVISIONER_MODE` stays `warmpool` (never attempt Modal live).
- If live creation is slow, pre-create the demo project and put live-creation on a vision slide.
- If anything breaks on stage, cut to the **backup video** and keep narrating. Never debug live.

---

## 8. Per-folder `CLAUDE.md` starter content (paste into each)

**`frontend/CLAUDE.md`**
> Next.js 14 App Router + TS + Tailwind + shadcn/ui. Import types ONLY from `lib/types.gen.ts`
> (generated; never edit). Read data from `lib/mockApi.ts`; swapping to `lib/api.ts` is one line.
> Dark theme, indigo #6D5EF7, Inter, 16px radius. SSE hooks parse `data: {json}` lines into contract
> unions. Keep components small. See root `ARCHITECTURE.md` + `TEAM_PLAN.md §2`.

**`backend/CLAUDE.md`**
> FastAPI + Pydantic v2 + async. Contracts live in `app/contracts/` and are FROZEN — import them,
> never redefine. Routers are THIN; logic lives in `control/`, `runtime/`, `provisioning/`,
> `connections/`, `ingestion/`. DB via `app/db/`. Build against `app/mocks/*` until the real
> dependency lands. AI only in shaping/compilation-freetext/ingestion-summary; provisioning is
> deterministic. Session-key convention is frozen (root `ARCHITECTURE.md §7`). See `TEAM_PLAN.md` for
> your section.

**`hermes/CLAUDE.md`**
> This folder holds the template profile, Composio MCP snippet, and gateway run/warm scripts. Profiles
> are stamped per project by `app/provisioning/hermes_writer.py`. Pin the Hermes version; disable
> self-update. Tool calls run on the gateway host — MCP binaries must be on its PATH. Model is set in
> `config.yaml` (Claude Sonnet 4.6), not in the request.

---

## 9. One-paragraph summary to read before you start

Freeze the contracts and schema in the first 45 minutes — they are the spine that lets five people
build separately. F builds the whole UX against a mock API. B1 builds the main agent (interview) and
the compiler (spec→files). B2 builds the FastAPI backbone, the swap-able runtime, and the provisioning
state machine that orchestrates everyone's output. C1 makes the user's real apps connectable via
Composio. C2 turns connections + a compiled bundle into a real, running, memory-seeded Hermes profile.
Before anyone builds shaping on top, B2+C1+C2 prove ONE hardcoded project end-to-end (Strava sports
coach). Then integrate upward along the pipeline at the checkpoints. The contracts package + generated
types + mock-first at every seam are what make "build separately, connect at the end" actually work.
