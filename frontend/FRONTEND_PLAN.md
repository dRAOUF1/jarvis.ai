# jarvis.ai — Frontend Build Bible (the F workstream)

> **You are the next Claude Code session.** This is the complete, self-contained plan to build the
> entire `frontend/` of jarvis.ai. Everything you need is here. Read it top-to-bottom once, then build
> in the **milestone order** in §16.
>
> **Ground truth:** the backend (B1/B2/C1/C2) is **fully implemented** on branches (`origin/Backend` is
> the consolidated source). The frontend is **greenfield** — every file under `frontend/` is currently a
> 0-byte stub and Next.js is not yet initialized. You build it from scratch.
>
> **The North Star:** A non-technical user talks to a main agent, shapes any project by conversation,
> watches it get "born" (provisioned + memory-seeded against their real apps), then chats with it. One
> user, many independent agents. **The UI/UX is the make-or-break of this project.**
>
> **Visual ambition (decided):** *Premium & polished* — Linear-meets-Raycast, Vercel-grade. Calm,
> confident, dark, indigo. Tasteful motion on enter/hover/stream. No gimmicks, no cinematic excess.
> Every screen demo-ready at **1280px** (projector resolution).

---

## 0. TL;DR — what you're building

Five screens, ~14 components, 2 SSE hooks, a typed API client with a mock twin, a design-token layer,
and a DiceBear avatar system. All built **mock-first** so the whole click-path works before any backend
is reachable; swapping to the real API is **one line per endpoint**.

| Route | Screen | Hero interaction |
|---|---|---|
| `/` | Dashboard | Grid of agent cards + "New agent" |
| `/create` | Shaping chat | Conversational interview with a **live spec card** assembling on the right |
| `/project/[id]/provisioning` | Provisioning | The state machine rendered as an agent being **born** |
| `/project/[id]/connections` | Connect apps | OAuth toggles, per-app tool reveal |
| `/project/[id]` | Project chat | Streaming markdown chat + **live memory/actions side panel** |

---

## 1. The API contract — exactly as the frontend sees it

> Extracted from the **real implemented backend** (`origin/Backend`), not the docs. Trust this section
> over ARCHITECTURE.md where they differ. Base URL in dev: `http://localhost:8000`. CORS is already
> open to `http://localhost:3000`.

### 1.1 REST + SSE endpoints

| Method | Path | Request body | Response | Notes |
|---|---|---|---|---|
| `POST` | `/projects/shape` | `{ message: string, history: {role,content}[] }` | **SSE** stream of `ShapingEvent` | Stateless: client resends full `history` each turn |
| `POST` | `/meta` | `{ need: string }` | `{ spec: ProjectSpec }` | One-shot need → spec (seed the chat or quick-create) |
| `POST` | `/projects` | `{ spec: ProjectSpec, connection_ids: string[] }` | `{ project: Project, handle: ProfileHandle }` | **Kicks off provisioning** server-side, returns immediately |
| `GET` | `/projects` | — | `{ projects: Project[] }` | For demo user (server uses `DEMO_USER_ID`) |
| `GET` | `/projects/:id` | — | `{ project: Project }` or `{ error }` | 200 with `{error}` on miss — **not** a 404 |
| `GET` | `/projects/:id/status` | — | `{ status: ProvisioningState, failed_stage?: string }` | **Poll this** during provisioning |
| `GET` | `/projects/:id/messages` | — | `{ messages: Message[] }` | History on chat mount |
| `POST` | `/projects/:id/chat` | `{ message: string }` | **SSE** stream of `RuntimeEvent` | Persists user+assistant msgs server-side |
| `GET` | `/catalog` | — | `{ apps: AppCatalogItem[] }` | ⚠️ shape mismatch — see §19.1 |
| `GET` | `/connections` | — | `{ connections: Connection[] }` | User-level, reused across projects |
| `POST` | `/connections` | `{ app: string }` | `{ connection: Connection, redirect_url?: string }` | Open `redirect_url` for OAuth |
| `GET` | `/connections/callback` | `?connection_id=` | 302 redirect | Composio → backend → back to frontend |
| `GET` | `/health` | — | `{ status, runtime_mode }` | Handy "is backend up" probe |

**Error convention to defend against:** several handlers return **HTTP 200 with `{ "error": "..." }`**
instead of a 4xx (e.g. `GET /projects/:id`, `POST /projects/:id/chat` with empty message). Your API
client must check for an `error` key on the parsed body, not just `res.ok`.

### 1.2 SSE wire format (both streams)

Each event is a line: `data: {json}\n\n`. The JSON is a **tagged union** discriminated by `type`.
The chat stream *also* sets the SSE `event:` field to the type (e.g. `event: delta`) — you can ignore
it and just parse `data`. Use a tolerant line parser (`EventSource` works, but we POST, so use
`fetch` + `ReadableStream` reader — see §9).

**Shaping stream — `POST /projects/shape` → `ShapingEvent`:**

```ts
| { type: "delta";       text: string }                                   // token of assistant prose
| { type: "question";    question: { field: string; prompt: string; options: string[] } }
| { type: "spec_update"; spec_update: Record<string, unknown> }           // partial ProjectSpec patch
| { type: "proposal";    spec: ProjectSpec; suggested_apps: string[] }    // interview complete
| { type: "done" }                                                        // turn complete
```

**Chat stream — `POST /projects/:id/chat` → `RuntimeEvent`:**

```ts
| { type: "delta";  text: string }                          // token of the agent's reply
| { type: "action"; label: string; detail?: string | null } // agent used a tool → toast + side panel
| { type: "done" }                                          // reply complete
| { type: "error";  message: string }                       // surface inline, end the stream
```

### 1.3 Data types (the frozen contracts → TypeScript)

These mirror `backend/app/contracts/models.py` exactly. The real `lib/types.gen.ts` is **generated**
from `/openapi.json` (see §3.4), but until the backend is running you hand-author this mirror as
`lib/types.ts` and import from there. When the backend is up, run `npm run gen:types` and migrate
imports to `lib/types.gen.ts` (keep the union event types — OpenAPI may flatten them awkwardly).

```ts
export type ProvisioningState =
  | "draft" | "compiling" | "connecting" | "provisioning" | "ingesting" | "ready" | "failed";

export type ConnectionStatus = "pending" | "connected" | "error";

export interface TaskItem { title: string; description: string; }

export interface ToolRequirement {
  app: string; reason: string; needed_scopes: string[]; tool_subset: string[];
}

export interface ProjectSpec {
  name: string;
  goal: string;
  persona: string;
  tasks: TaskItem[];
  tool_requirements: ToolRequirement[];
  success_criteria: string[];
  avatar_seed: string;
}

export interface Project {
  id: string;
  user_id: string;
  name: string;
  goal: string | null;
  status: ProvisioningState;
  failed_stage: string | null;
  spec: ProjectSpec | null;
  avatar_seed: string | null;
}

export interface Connection {
  id: string;
  user_id: string;
  app: string;
  status: ConnectionStatus;
  mcp_url: string | null;
  available_tools: string[];
}

export interface ProfileHandle {
  project_id: string; gateway_url: string; gateway_key: string;
  session_key: string; runtime_key: string; status: ProvisioningState;
}

// Catalog: the CONTRACT shape is below, but the live endpoint may emit a different shape — see §19.1.
// Normalize both into this app-facing shape in the API client.
export interface CatalogApp {
  app: string;          // stable id, e.g. "strava"
  display_name: string; // "Strava"
  description: string;
  icon: string;         // emoji in current backend, e.g. "🏃"
  default_scopes: string[];
  default_tools?: string[]; // present only on the catalog.py shape (default_tool_subset)
}

export interface Message { id: string; project_id: string; role: "user" | "assistant"; content: string; created_at: string; }

// SSE unions (see §1.2)
export type ShapingEvent =
  | { type: "delta"; text: string }
  | { type: "question"; question: { field: string; prompt: string; options: string[] } }
  | { type: "spec_update"; spec_update: Partial<ProjectSpec> & Record<string, unknown> }
  | { type: "proposal"; spec: ProjectSpec; suggested_apps: string[] }
  | { type: "done" };

export type RuntimeEvent =
  | { type: "delta"; text: string }
  | { type: "action"; label: string; detail?: string | null }
  | { type: "done" }
  | { type: "error"; message: string };
```

### 1.4 The app catalog (current backend data — 8 apps)

`strava 🏃` · `gmail 📧` · `apple_health ❤️` · `github 🐙` · `notion 📝` · `slack 💬` ·
`google_calendar 📅` · `spotify 🎵`. Each has `description`, `default_scopes`, and a tool subset.
**Strava is the canonical demo app** (sports-coach hero path). Hard-code a richer per-app presentation
map in the frontend (brand color + lucide icon fallback) keyed by `app` id — see §15.3.

---

## 2. Tech stack & dependencies (decided)

```
Next.js 14 (App Router) · TypeScript (strict) · Tailwind CSS · shadcn/ui · lucide-react
framer-motion (motion, used lightly) · sonner (action toasts) · react-markdown + remark-gfm
@dicebear/core + @dicebear/collection (agent avatars) · openapi-typescript (dev, type-gen)
clsx + tailwind-merge (cn helper) · @tanstack/react-query (server-state for REST; NOT for SSE)
```

Rationale for the additions beyond the decided base:
- **sonner** — the agent's `action` events become elegant, auto-stacking toasts ("🏃 Fetched your last run").
- **react-markdown + remark-gfm** — agent replies render as real markdown (code, lists, bold), streamed.
- **@dicebear** — deterministic unique avatar per agent from `avatar_seed`. Style: `shapes` or `glass`
  (abstract, premium, on-brand) — **not** the cartoon `bottts`. Pick `glass` for the calm aesthetic.
- **@tanstack/react-query** — caches `/projects`, `/catalog`, `/connections`, drives the status poll
  with `refetchInterval`. SSE streams bypass it (handled by the two custom hooks).

> Do **not** add a component kit beyond shadcn/ui. Do **not** add a CSS-in-JS lib. Tailwind + tokens only.

---

## 3. Project setup (exact, do this first)

### 3.1 Scaffold

```bash
cd frontend
npx create-next-app@latest . \
  --typescript --tailwind --eslint --app --src-dir=false --import-alias "@/*" --no-turbo
# Keep app/ at frontend/app (no src dir) to match the frozen layout.
npm i framer-motion sonner react-markdown remark-gfm @dicebear/core @dicebear/collection \
      clsx tailwind-merge @tanstack/react-query
npm i -D openapi-typescript
npx shadcn@latest init   # base color: neutral/slate; CSS variables: yes
npx shadcn@latest add button card input textarea badge avatar scroll-area separator \
      dialog tooltip skeleton switch tabs sonner
```

### 3.2 `package.json` scripts

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "gen:types": "openapi-typescript http://localhost:8000/openapi.json -o lib/types.gen.ts"
  }
}
```

### 3.3 Env

```
# frontend/.env.local
NEXT_PUBLIC_API_BASE=http://localhost:8000
NEXT_PUBLIC_USE_MOCK=true   # flip to false when the backend is reachable
```

The single mock/real switch lives in `lib/api.ts` (§9.4): one ternary reading `NEXT_PUBLIC_USE_MOCK`.

### 3.4 Type generation

Until the backend runs, use the hand-authored `lib/types.ts` (§1.3). Once `http://localhost:8000` is
up: `npm run gen:types`. Keep the SSE union types in `lib/types.ts` regardless (OpenAPI flattens unions
poorly); import data models from `types.gen.ts`. Never hand-edit `types.gen.ts`.

---

## 4. Design tokens — `lib/design/tokens.css`

The single source of visual truth. Imported once in `app/globals.css`. Wire these CSS variables into
`tailwind.config.ts` so utilities like `bg-bg-1`, `text-fg-2`, `rounded-card` work.

```css
:root {
  /* ---- Surfaces (dark, layered — never pure black) ---- */
  --bg-0: #0B0B0F;   /* app background, deepest */
  --bg-1: #121218;   /* primary surface / cards */
  --bg-2: #1A1A22;   /* raised surface / inputs / hover */
  --bg-3: #23232E;   /* popovers, active rows */
  --stroke: #2A2A35; /* hairline borders */
  --stroke-strong: #3A3A48;

  /* ---- Foreground ---- */
  --fg-0: #F4F4F6;   /* primary text */
  --fg-1: #B8B8C4;   /* secondary text */
  --fg-2: #6E6E7E;   /* muted / captions */

  /* ---- Brand (indigo) ---- */
  --accent: #6D5EF7;
  --accent-hover: #5B4DE0;
  --accent-soft: rgba(109, 94, 247, 0.14);   /* tints, glows, selected bg */
  --accent-ring: rgba(109, 94, 247, 0.45);

  /* ---- Status ---- */
  --ok: #3FB950; --warn: #D29922; --err: #F85149; --info: #58A6FF;

  /* ---- Radius (16px hero radius) ---- */
  --r-sm: 8px; --r-md: 12px; --r-card: 16px; --r-lg: 20px; --r-pill: 999px;

  /* ---- Elevation (soft, low-contrast) ---- */
  --shadow-1: 0 1px 2px rgba(0,0,0,.4);
  --shadow-2: 0 8px 30px rgba(0,0,0,.35);
  --shadow-glow: 0 0 0 1px var(--accent-ring), 0 8px 40px rgba(109,94,247,.25);

  /* ---- Motion ---- */
  --ease-out: cubic-bezier(.16,1,.3,1);     /* the signature Linear ease */
  --ease-in-out: cubic-bezier(.45,0,.55,1);
  --dur-1: 120ms; --dur-2: 200ms; --dur-3: 360ms; --dur-4: 600ms;

  /* ---- Type ---- */
  --font-sans: "Inter", ui-sans-serif, system-ui, sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, monospace;
}
```

**Type scale** (Inter, `-0.011em` tracking on headings, `1.5`/`1.6` line-height on body):
`display 32/40 600` · `h1 24/32 600` · `h2 20/28 600` · `h3 16/24 600` · `body 15/24 400` ·
`small 13/20 400` · `caption 12/16 500 uppercase tracking-wide` · `mono 13/20`.

**Spacing:** 4px base grid (`4 8 12 16 20 24 32 40 56 64`). Page gutters `32px` at 1280. Card padding
`20–24px`. Cozy, not cramped.

Load **Inter** via `next/font/google` (weights 400/500/600), `JetBrains Mono` 400/500 for code/keys.

---

## 5. Design language (the rules that make it "premium")

1. **Calm > busy.** Lots of negative space. One accent color, used sparingly — indigo earns attention
   only on the primary action and active state. Everything else is grayscale.
2. **Hairlines, not boxes.** `1px var(--stroke)` borders + subtle `--bg-1/2/3` layering for depth.
   Shadows are soft and rare; reserve `--shadow-glow` for the focused agent / "ready" moment.
3. **Motion is feedback, never decoration.** Animate on **enter, hover, state-change, stream** only.
   Durations 120–360ms with `--ease-out`. Respect `prefers-reduced-motion` (disable transforms, keep
   opacity). No looping ambient animation except the provisioning "breathing" state.
4. **Typography does the hierarchy.** Weight + size + color, not borders/badges, separate levels.
5. **Never a blank screen.** Every async surface has skeleton → content, and a designed empty state.
6. **Keyboard-first feel.** `⌘K`-style affordances optional, but: Enter to send, `⌘↵` newline,
   visible focus rings (`--accent-ring`), Esc closes dialogs.
7. **Density target:** comfortable at 1280×800. Test every screen at exactly 1280px wide.

---

## 6. Information architecture & app shell

```
app/
  layout.tsx            # <html> dark, font vars, <Providers/> (React Query + <Toaster/>), AppShell
  globals.css           # imports tokens.css + Tailwind layers + base resets
  page.tsx              # Dashboard
  create/page.tsx       # Shaping chat
  project/[id]/page.tsx                 # Project chat + side panel
  project/[id]/provisioning/page.tsx    # Provisioning progress
  project/[id]/connections/page.tsx     # Connect apps
  providers.tsx         # "use client" — QueryClientProvider + Sonner <Toaster richColors/>
```

**App shell (`AppShell`):** a slim top bar — left: `jarvis` wordmark (links to `/`), center: contextual
breadcrumb (agent name on project routes), right: the demo user avatar + a `mock/live` pill bound to
`NEXT_PUBLIC_USE_MOCK` (so on stage you can prove which engine is running). No heavy sidebar — this is a
focused, few-screens app; keep chrome minimal. Max content width `1200px`, centered, `32px` gutters.

**Navigation flow:**
`/` → "New agent" → `/create` → (proposal accepted, `POST /projects`) → `/project/[id]/provisioning`
→ (auto-advances on `ready`) → `/project/[id]`. The connections screen is reachable from the create
flow (before provisioning, to authorize apps) and from a project's header (to manage apps later).

---

## 7. Component inventory

Build in `components/`. Each is small, typed, client/server-correct (`"use client"` only where it uses
state/effects/handlers). Props sketched; refine against `lib/types.ts`.

| Component | Purpose | Key props | States to handle |
|---|---|---|---|
| `AppShell` | top bar + page frame | `{children}` | mock/live pill |
| `AgentAvatar` | DiceBear avatar from seed | `{seed, size, ring?}` | deterministic; ring on hover/ready |
| `StatusDot` | colored dot + label for `ProvisioningState`/`ConnectionStatus` | `{state, pulse?}` | per-state color (§15.2), pulse while transient |
| `ProjectCard` | one agent on the dashboard | `{project}` | ready / provisioning(animated) / failed; hover lift |
| `ProjectGrid` | responsive grid + "New agent" tile | `{projects}` | empty, skeleton, loaded |
| `NewProjectCard` | dashed "＋ New agent" tile | — | hover glow |
| `ShapingChat` | the interview thread + composer | `{onProposal}` | streaming, question-chips, error |
| `SpecCard` | live-assembling ProjectSpec preview | `{spec, suggestedApps}` | partial→complete fill animation |
| `QuestionChips` | quick-reply option buttons from `question` event | `{options, onPick}` | selected, disabled-after-pick |
| `ProvisioningProgress` | the FSM as a vertical "birth" timeline | `{status, failedStage}` | per-stage pending/active/done/failed |
| `ConnectionToggle` | one app row w/ connect/connected + tool reveal | `{app, connection, onConnect}` | pending/connected/error, OAuth-pending |
| `ChatThread` | message list, streaming markdown | `{messages, streamingText}` | empty, streaming cursor, autoscroll |
| `MessageBubble` | one message (markdown) | `{role, content, streaming?}` | user vs assistant styling |
| `Composer` | textarea + send, Enter/⌘↵ | `{onSend, disabled}` | disabled while streaming, autosize |
| `SidePanel` | memory chips + recent actions | `{memory, actions}` | empty, live-append on action |
| `TypingCursor` | the blinking stream caret | — | reduced-motion → static |
| `Skeleton*` | per-surface loaders | — | shimmer |

---

## 8. Screen specs (the heart of the build)

### 8.1 Dashboard — `app/page.tsx`

**Purpose:** see all your agents; make a new one.

- **Layout:** page title row — `h1 "Your agents"` + subtle count, right-aligned `New agent` button
  (`+` icon, accent). Below: `ProjectGrid` — `grid-cols-3` at 1280 (`gap-20`), responsive down to 1.
- **`ProjectCard`:** `--bg-1`, `--r-card`, `1px --stroke`. Top-left `AgentAvatar` (48px). Title (`h3`)
  + one-line `goal` (`fg-1`, truncate 2 lines). Bottom row: connected-app icon stack (small) + a
  `StatusDot`. Hover: lift `translateY(-2px)`, border → `--stroke-strong`, faint `--shadow-2`
  (`--dur-2 --ease-out`). Click → if `ready` go to chat; if `provisioning/compiling/...` go to the
  provisioning view; if `failed` go to provisioning view (which shows retry).
- **Provisioning card variant:** show an animated `StatusDot` (pulsing) + the current stage label
  ("Ingesting…") and a thin indeterminate accent bar along the card bottom. Make "still cooking" feel
  alive, not broken.
- **`NewProjectCard`:** dashed `--stroke` tile, centered `+` glyph + "New agent", hover → accent glow
  border + `--accent-soft` fill. Links to `/create`.
- **States:** **loading** → 6 `Skeleton` cards (shimmer). **empty** → centered illustration-lite block:
  big `+`, "No agents yet", "Shape your first one →" CTA. **error** → quiet inline retry.
- **Data:** React Query `['projects']` → `api.listProjects()`. Optimistic insert when returning from
  create (the new project appears immediately in `provisioning` state).

### 8.2 Shaping chat — `app/create/page.tsx` (the signature screen)

**Purpose:** the magic. User types a vague wish; the main agent interviews them; a **spec card builds
itself on the right** in real time; on `proposal`, they pick apps and create.

- **Layout (two-pane at ≥1024px):** left ~60% `ShapingChat`, right ~40% sticky `SpecCard`. Below 1024,
  SpecCard collapses into a peekable bottom sheet / drawer. At 1280 this two-pane is the hero view.
- **`ShapingChat`:**
  - Empty state: a warm prompt — "What do you want an agent for?" + 3 example chips
    ("A sports coach", "An inbox triager", "A daily journal companion") that prefill the composer.
  - On send: optimistic user bubble, then open SSE `useShapingStream`. Render `delta` tokens into a
    streaming assistant bubble with `TypingCursor`.
  - On `question` event: render the prose, then `QuestionChips` for `options` (plus the composer stays
    open for free-text). Picking a chip sends it as the next message. Chips animate in (`stagger 40ms`).
  - On `spec_update`: **do not** print it in chat — route the partial into the `SpecCard` (see below),
    and show a tiny inline "✓ noted: <field>" affordance so the user feels heard.
  - On `proposal`: render a celebratory **ProposalCard** inline — the finalized spec summary + the
    `suggested_apps` as selectable `ConnectionToggle`-lite chips (default all on) + a primary
    **"Create agent"** button.
- **`SpecCard` (right pane):** a live preview of the `ProjectSpec` as it fills. Sections: avatar +
  `name`, `goal`, `persona` (italic, fg-1), `tasks` (checklist), `success_criteria` (bullets),
  `tool_requirements` (app chips). Each field, when first populated by a `spec_update`/`proposal`,
  does a soft **highlight-then-settle** (`--accent-soft` flash → fade, `--dur-3`) and height
  auto-animates (framer `layout`). Before any data: ghost/skeleton rows labeled with field names so the
  user sees the "shape" of what they're filling. The avatar uses `spec.avatar_seed` once present.
- **Create action:** `POST /projects { spec, connection_ids }`. `connection_ids` = the connections the
  user has authorized for the chosen apps. If a chosen app isn't connected yet → route to
  `/project/[id]/connections` first (or inline-OAuth), then create. For the demo/mock path, allow
  creating with zero connections (backend falls back to mock connections). On success → push to
  `/project/[id]/provisioning`.
- **Seeding shortcut:** offer a "Quick build" affordance that calls `POST /meta {need}` to jump straight
  to a `proposal`-style SpecCard without the full interview (useful if a turn is slow on stage).
- **States:** stream error → inline "the agent hiccuped, retry" with the last user message re-sendable.
  Mid-stream the composer is disabled with a subtle "thinking…" shimmer on the send button.

### 8.3 Provisioning progress — `app/project/[id]/provisioning/page.tsx` (the "birth" moment)

**Purpose:** turn a 10–40s wait into the most delightful 30 seconds of the demo. This is where
"premium" pays off.

- **Center stage:** the agent's `AgentAvatar` (large, 96px) inside a **breathing halo** — a soft
  `--accent` radial glow that gently scales/opacity-pulses (`--dur-4`, ease-in-out, infinite) while
  work is in flight, and snaps to a crisp `--shadow-glow` ring + a one-time bloom on `ready`.
- **The FSM timeline** (vertical, left-aligned under the avatar) renders the 5 stages from the contract,
  in order:
  | Stage | Label shown | Sub-copy |
  |---|---|---|
  | `compiling` | "Designing the agent" | "Writing its soul and skills" |
  | `connecting` | "Linking your apps" | "Securing tool access" |
  | `provisioning` | "Building the runtime" | "Spinning up a private gateway" |
  | `ingesting` | "Learning about you" | "Reading your recent activity" |
  | `ready` | "Ready" | "Say hello 👋" |
  Each row: a leading node (pending = hollow `--stroke`, active = pulsing accent, done = filled accent
  check, failed = `--err` cross) + label + sub-copy. The connector line fills accent as stages complete
  (animated height). Active row's sub-copy can cycle gentle status phrases.
- **Driver:** React Query `['status', id]` with `refetchInterval: 900ms` until `status==='ready' || 'failed'`.
  Map the returned `status` onto the timeline; everything **before** the current stage = done, current =
  active, after = pending. (The backend advances through states server-side; you only read.)
- **On `ready`:** halo blooms, a one-shot success chime is **not** used (sound was declined), instead a
  satisfying scale-in of a "Start chatting →" primary button + confetti-free accent ripple. Auto-redirect
  to `/project/[id]` after ~1.2s (or on click).
- **On `failed`:** show `failed_stage` mapped to a friendly message, a "Retry" button (re-`POST /projects`
  or a retry endpoint if added), and a "Switch to safe mode" hint (mock). Keep it calm, not alarming.
- **States:** if status fetch errors, keep last known stage and show a subtle "reconnecting" chip; never
  flash the timeline back to empty.

### 8.4 Connections — `app/project/[id]/connections/page.tsx`

**Purpose:** authorize the real apps (Composio OAuth). User-level connections, reused across agents.

- **Layout:** `h1 "Connect your apps"` + sub "Authorize once, reuse everywhere." A list/grid of
  `ConnectionToggle` rows, one per catalog app. The apps this project *needs* (from spec
  `tool_requirements` / `suggested_apps`) float to the top with a "Recommended" tag.
- **`ConnectionToggle`:** left — app icon (brand color chip, §15.3) + display name + "what it does".
  Right — a `Switch`/button: **Connect** (accent) when unconnected; **Connected** (✓, `--ok`) when done;
  **Error** (retry) on failure. Expanding a connected row reveals its `available_tools` as small mono
  chips ("get_activities", …) so the user sees the granted capability — a trust-building detail.
- **OAuth flow:** click Connect → `POST /connections {app}` → if `redirect_url`, open it
  (`window.location` or a popup) → Composio → backend `/connections/callback` redirects back here with
  `?connection_id=`. On mount, read that query param, refetch `/connections`, flip the row to Connected
  with a check animation + a toast "Strava connected 🎉". **Poll/refetch** `/connections` on focus to
  catch popup-completed auths.
- **Mock path:** in mock mode, Connect resolves to `connected` after a 700ms fake delay (no real
  redirect) so the whole flow demos offline.
- **States:** loading → skeleton rows; per-row connecting spinner; error → inline retry; success toast.

### 8.5 Project chat — `app/project/[id]/page.tsx` (the payoff)

**Purpose:** talk to the finished agent; watch it remember and act.

- **Layout (two-pane):** left ~68% `ChatThread` + `Composer` pinned bottom; right ~32% `SidePanel`.
  Header strip: `AgentAvatar` + agent name + `StatusDot(ready)` + a "Manage apps" link → connections.
- **`ChatThread`:**
  - On mount: `GET /projects/:id/messages` → render history. Empty → a friendly first-run prompt from
    the agent's persona ("Hey, I'm your coach. Ask me how your last run went.") + suggestion chips.
  - Send via `Composer` → optimistic user `MessageBubble` → open `useAgentStream`. `delta` tokens stream
    into the assistant bubble rendered as **markdown** (`react-markdown` + `remark-gfm`), with a
    `TypingCursor` at the tail while streaming. Auto-scroll to bottom unless the user has scrolled up
    (then show a "↓ new" pill).
  - `action` events: fire a **sonner toast** (`label`, with `detail` as description, an app-tinted icon)
    *and* append to the SidePanel "Recent actions". This is the "it's really doing things" wow.
  - `error` event: inline error chip in the thread, re-enable composer.
- **`MessageBubble`:** user = right-aligned, `--bg-2`, `--r-md`; assistant = left-aligned, no bubble
  (full-width prose) or subtle `--bg-1` card — choose the cleaner: **assistant as full-width markdown,
  user as a contained bubble** (ChatGPT/Linear style). Avatar gutter on assistant rows.
- **`Composer`:** autosizing `Textarea`, Enter = send, `⌘/Ctrl+↵` = newline, send button enables only
  with content, disabled+shimmer while a stream is open. Placeholder cycles helpful prompts.
- **`SidePanel`:** two stacked sections. **Memory** — chips/cards of what the agent knows (seed from
  ingestion; in mock mode read `mock_runtime_data`). Kinds (`fact`/`preference`/`scraped`/`weakness`)
  get distinct subtle tints. **Recent actions** — a timeline of `action` events this session, newest on
  top, each animating in (`slide+fade`, `--dur-2`). Empty states for both. The panel is what sells
  "memory + agency" to the judges — make it feel live.
- **States:** loading history → skeleton bubbles; reconnect on stream drop; never lose the user's typed
  draft on error.

---

## 9. The SSE hooks (`lib/useShapingStream.ts`, `lib/useAgentStream.ts`)

Both POST and read a streamed body, so **don't use `EventSource`** (it's GET-only). Use
`fetch` + `response.body.getReader()` + a `TextDecoder`, buffering by `\n\n` and parsing `data:` lines.

### 9.1 Shared SSE reader util (`lib/sse.ts`)

```ts
// Yields each parsed JSON event object from an SSE POST response.
export async function* sseStream<T>(res: Response): AsyncGenerator<T> {
  const reader = res.body!.getReader();
  const dec = new TextDecoder();
  let buf = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    let i: number;
    while ((i = buf.indexOf("\n\n")) !== -1) {
      const frame = buf.slice(0, i); buf = buf.slice(i + 2);
      for (const line of frame.split("\n")) {
        const t = line.trim();
        if (t.startsWith("data:")) {
          const json = t.slice(5).trim();
          if (json && json !== "[DONE]") yield JSON.parse(json) as T;
        }
      }
    }
  }
}
```

### 9.2 `useShapingStream`

Returns `{ messages, streamingText, partialSpec, proposal, suggestedApps, status, send() }`.

- `send(message)`: append optimistic user message, set `status="streaming"`, POST
  `/projects/shape { message, history }`, iterate `sseStream<ShapingEvent>`:
  - `delta` → append to `streamingText`.
  - `question` → store current question (prose already in `streamingText`); expose `options` to the UI.
  - `spec_update` → deep-merge `spec_update` into `partialSpec` (it's a partial patch).
  - `proposal` → set `proposal=spec`, `suggestedApps`, finalize `partialSpec=spec`.
  - `done` → flush `streamingText` into a committed assistant message; `status="idle"`.
- Maintains `history` (role/content) internally and resends it each turn (backend is stateless).
- On network error → `status="error"`, keep the last user message for retry.

### 9.3 `useAgentStream`

Returns `{ messages, streamingText, actions, status, send() }`.

- On mount, optionally hydrate `messages` from `GET /projects/:id/messages`.
- `send(message)`: optimistic user bubble, POST `/projects/:id/chat { message }`, iterate
  `sseStream<RuntimeEvent>`:
  - `delta` → append to `streamingText`.
  - `action` → push `{label, detail, ts}` to `actions` **and** call an `onAction` callback (the page
    wires this to `toast(...)`).
  - `done` → commit `streamingText` to a message; clear it.
  - `error` → expose `error`, stop.
- The page persists nothing (backend persists messages); on next mount, history reloads from the server.

### 9.4 `lib/api.ts` + `lib/mockApi.ts`

- `api.ts` exports a typed client: `listProjects`, `getProject`, `createProject`, `getStatus`,
  `getMessages`, `getCatalog`, `listConnections`, `connect`, plus `shapeStreamURL()` /
  `chatStreamURL(id)` helpers (the hooks build the `fetch` themselves but get the URL/headers here).
  Every method checks for the `{error}`-in-200 convention and throws a typed `ApiError`.
- `getCatalog()` **normalizes** both catalog shapes into `CatalogApp` (§19.1).
- `mockApi.ts` mirrors the same signatures with in-memory fixtures + async delays, including
  `mockShapeStream()` and `mockChatStream()` async generators that emit realistic event sequences for
  the Strava sports-coach script (see §10). A single `export const api = USE_MOCK ? mockApi : realApi`
  in `lib/api.ts` is the **one-line swap** (per the team plan). Even finer: swap per-method if a backend
  route lands before others.

---

## 10. The mock layer (build against this first)

Make the **entire click-path** work with `NEXT_PUBLIC_USE_MOCK=true` and no backend. Fixtures:

- **`mockProjects`**: 2–3 agents incl. one `ready` "Sports Coach" (Strava avatar_seed), one mid
  `provisioning` to show the animated card.
- **`mockCatalog`**: the 8 apps from §1.4 (frontend-owned copy; doesn't depend on the backend bug).
- **`mockConnections`**: Strava `connected`, others `pending`.
- **`mockShapeStream(message, history)`**: scripted sports-coach interview — emits `delta` prose, a
  `question` ("Which sport?" options), `spec_update`s that progressively fill name/goal/persona/tasks,
  then a `proposal` with `suggested_apps:["strava","apple_health"]`. Time the chunks (20–40ms) so it
  *feels* like a live model.
- **`mockChatStream(message)`**: streams a coach reply token-by-token incl. one `action`
  (`label:"Fetched your last run", detail:"12.4km · 53:20 · avg 4:18/km"`) then `done`. Make the reply
  reference "memory" so the side panel feels real.
- **`mockStatusProgression(id)`**: returns advancing states on each poll (compiling→…→ready over ~6s)
  so the provisioning cinematic plays offline. Use a per-id start-timestamp to compute the stage.
- **`mockMemory`**: a handful of `fact`/`preference`/`scraped` entries for the SidePanel.

This is the demo-morning insurance for the *frontend*: even if every backend is down, the click-path and
the visuals are intact.

---

## 11. State management

- **Server state (REST):** React Query. Keys: `['projects']`, `['project', id]`, `['status', id]`
  (polling), `['messages', id]`, `['catalog']`, `['connections']`. Mutations: `createProject`,
  `connect` (invalidate the relevant keys; optimistic where it improves feel).
- **Stream state (SSE):** the two custom hooks own local `useReducer` state (messages, streamingText,
  actions). Don't shove streaming tokens through React Query.
- **UI state:** local `useState`. No global store needed — the app is shallow. If cross-route state is
  wanted (e.g. the just-shaped spec handed to create), pass via the create flow's own state or a tiny
  `sessionStorage` bridge; prefer creating server-side immediately and navigating by `id`.

---

## 12. Motion & micro-interactions (framer-motion, used lightly)

- **Route/section enter:** `opacity 0→1`, `y 8→0`, `--dur-3 --ease-out`. Stagger lists by 30–50ms.
- **Cards:** hover lift (`y:-2`, shadow), `--dur-2`. Press → `scale .99`.
- **SpecCard fields:** `layout` animation for height; `--accent-soft` highlight flash on populate.
- **Provisioning halo:** the one allowed infinite animation — gentle `scale 1→1.04` + opacity pulse.
- **Streaming cursor:** 1px caret, blink `1s steps(2)`; hidden under `prefers-reduced-motion`.
- **Toasts:** sonner defaults, `richColors`, top-right, app-tinted icon, 4s.
- **Reduced motion:** wrap a `useReducedMotion()` check; degrade transforms to opacity-only, kill the
  halo pulse and caret blink. Never block content on animation.

Keep total motion budget low: if it doesn't communicate state, cut it.

---

## 13. Accessibility & responsiveness

- **Target 1280px** (projector) as the design canvas; verify 1024 and 1440 don't break. Mobile is
  best-effort (single column, SpecCard/SidePanel become drawers) — not a demo target but don't crash.
- Color contrast ≥ WCAG AA on text (`--fg-0/1` on `--bg-0/1` pass; keep captions ≥ `--fg-2` only on
  large/secondary text). Don't encode state by color alone — pair `StatusDot` color with a label.
- Keyboard: focus rings everywhere (`--accent-ring`), logical tab order, Esc closes dialogs, Enter
  sends. ARIA live region for streaming assistant text and for status changes.
- Respect `prefers-reduced-motion` (§12). Alt text on avatars (agent name).

---

## 14. Build milestones (do them in this order)

> Mirrors TEAM_PLAN §2 "Order of work," refined. Each milestone is independently demoable against mock.

1. **M0 — Foundation.** Scaffold (§3), tokens + Tailwind wiring (§4), `AppShell`, `Providers`, fonts,
   `lib/types.ts`, `cn` helper, shadcn primitives, sonner Toaster. *Done = blank app renders dark,
   on-brand, with the top bar and a mock/live pill.*
2. **M1 — Mock layer + API client.** `lib/api.ts` (+ `mockApi.ts`), `lib/sse.ts`, all fixtures (§10).
   *Done = you can call every method in a scratch page and see fixture data.*
3. **M2 — Dashboard.** `ProjectGrid`, `ProjectCard`, `NewProjectCard`, `AgentAvatar`, `StatusDot`,
   skeletons, empty state. *Done = grid of mock agents, animated provisioning card, navigates correctly.*
4. **M3 — Shaping chat.** `useShapingStream`, `ShapingChat`, `SpecCard`, `QuestionChips`, ProposalCard,
   example chips. *Done = full mock interview → spec assembles live → "Create agent".*
5. **M4 — Provisioning.** `ProvisioningProgress` + halo + status polling against `mockStatusProgression`.
   *Done = the birth cinematic plays end-to-end → auto-routes to chat on ready.*
6. **M5 — Connections.** `ConnectionToggle`, OAuth-redirect handling + mock connect. *Done = authorize
   Strava (mock + real-redirect), tools reveal, toast.*
7. **M6 — Project chat.** `useAgentStream`, `ChatThread`, `MessageBubble` (markdown), `Composer`,
   `SidePanel`, action toasts. *Done = streamed markdown reply + action toast + side panel updates live.*
8. **M7 — Wire to real backend.** Bring up `origin/Backend`, `npm run gen:types`, flip
   `NEXT_PUBLIC_USE_MOCK=false`, fix each endpoint (catalog normalize §19.1, `{error}`-in-200, session
   behaviors). Swap per-endpoint as routes prove green.
9. **M8 — Polish pass.** Spacing audit at 1280, motion timing, empty/error/loading states, focus rings,
   reduced-motion, copy. Make it *beautiful*, not just done.

---

## 15. Reference details

### 15.1 Provisioning stage → copy map
See the table in §8.3. Keep sub-copy human and confident; never expose raw enum names.

### 15.2 Status colors
`draft → fg-2` · `compiling/connecting/provisioning/ingesting → accent (pulsing)` · `ready → ok` ·
`failed → err`. Connections: `pending → warn` · `connected → ok` · `error → err`.

### 15.3 Per-app presentation map (frontend-owned, keyed by `app` id)
Give each app a brand tint + lucide fallback icon (backend ships emoji — render emoji *or* this map):
`strava → #FC4C02 (Activity)` · `gmail → #EA4335 (Mail)` · `apple_health → #FF2D55 (HeartPulse)` ·
`github → #FFFFFF (Github)` · `notion → #FFFFFF (FileText)` · `slack → #4A154B (MessageSquare)` ·
`google_calendar → #4285F4 (Calendar)` · `spotify → #1DB954 (Music)`. Unknown app → `accent (Plug)`.

### 15.4 DiceBear avatar
`createAvatar(glass, { seed }).toDataUri()` memoized by seed in `AgentAvatar`. Fall back to a gradient
monogram from the seed if generation fails. Wrap in a rounded-`--r-md` frame; add a `--shadow-glow` ring
on hover and on a `ready` agent.

---

## 16. Definition of done (the demo gate)

The full click-path works **against mock with zero backend**, and again **against the real backend**
with only the one-line swap + per-endpoint fixes:

1. Dashboard shows agents; "New agent" → shaping.
2. Shape a project conversationally; the spec card assembles live; accept the proposal.
3. Watch the provisioning "birth" run the 5 stages to `ready`.
4. Connect an app via OAuth toggles (Strava), see its tools.
5. Chat with the agent: streamed markdown reply, an action toast fires, the side panel updates live.
6. Everything looks beautiful and intentional at **1280px**. No blank/janky states. Reduced-motion safe.

---

## 17. Known risks & gotchas (read before wiring real backend — M7)

### 17.1 ⚠️ Catalog shape mismatch (will bite you)
`backend/app/control/catalog.py` defines `AppCatalogItem` as `{id, name, description, icon,
default_tool_subset, default_scopes}`, but the **contract** `AppCatalogItem` the `/catalog` endpoint
declares is `{app, display_name, description, icon, default_scopes}`. The live JSON may come back in
*either* shape (or FastAPI may 500 on the response_model validation). **Defend in `getCatalog()`:**
normalize with `app: x.app ?? x.id`, `display_name: x.display_name ?? x.name`,
`default_tools: x.tool_subset ?? x.default_tool_subset ?? []`. Keep your **own** `mockCatalog` as the
source of truth for the demo so a backend catalog bug never blocks the UI.

### 17.2 `{error}` returned with HTTP 200
`GET /projects/:id`, `POST /chat` (empty msg), etc. return `200 {"error": "..."}` not a 4xx. The API
client must inspect the body for `error` and throw, or screens will render undefined.

### 17.3 Session-key / memory
Memory persistence hinges on the backend's `X-Hermes-Session-Key = agent:{project_id}:user:{user_id}`.
The frontend doesn't set it (the backend does from the project row), but **verify memory recall at M7**:
chat, mention a fact, reload, ask again. If it forgets, it's a backend session-key bug — flag it.

### 17.4 SSE through dev proxies / buffering
`sse-starlette` streams fine, but if you add a Next.js rewrite/proxy, disable response buffering. Prefer
hitting `NEXT_PUBLIC_API_BASE` directly (CORS is already open) over proxying, to keep streams snappy.

### 17.5 `connection_ids` vs apps
`POST /projects` wants `connection_ids` (Connection UUIDs), **not** app ids. Map chosen apps →
their connected `Connection.id` before creating. If an app isn't connected, send it through
connections first (or, for the mock/demo path, create with `[]` — backend falls back to mock
connections).

### 17.6 Provisioning is server-driven
You only **poll** `/status`; the backend advances the FSM. Don't try to drive stages from the client.
If the backend jumps straight to `ready` (fast warm pool), still play a minimum ~2.5s of the cinematic
so the moment lands (gate the auto-advance on `max(real, 2500ms)`).

---

## 18. Kickoff prompt for the next Claude Code session

> You are building the entire Next.js 14 App Router frontend for **jarvis.ai** in `frontend/`. Read
> `frontend/FRONTEND_PLAN.md` (this file) fully first, then the root `ARCHITECTURE.md` for context. The
> backend is already implemented (`origin/Backend`); the frontend is greenfield. Build **mock-first** so
> the whole click-path works with `NEXT_PUBLIC_USE_MOCK=true` and no backend, then wire the real API with
> a one-line swap. Stack: Next 14 + TS strict + Tailwind + shadcn/ui + framer-motion (light) + sonner +
> react-markdown + @dicebear. Design: dark, indigo `#6D5EF7`, Inter, 16px radius, Linear-meets-Raycast,
> *premium & polished* — tasteful motion on enter/hover/stream only, never a blank screen, beautiful at
> 1280px. Import types from `lib/types.ts` (or `lib/types.gen.ts` once generated). Build in the milestone
> order in §14 (M0→M8). The signature screens are the **shaping chat with a live-assembling spec card**
> (§8.2) and the **provisioning "birth" cinematic** (§8.3) — make those sing. Watch the gotchas in §17
> (catalog shape mismatch, `{error}`-in-200, `connection_ids` vs apps). Keep components small and
> accessible; respect `prefers-reduced-motion`. Commit in small steps. After each milestone, confirm the
> mock click-path still runs end-to-end.

---

*Built from the real backend contracts on `origin/Backend` (commit-accurate as of this branch). If a
contract changes upstream, re-run `npm run gen:types` and reconcile §1.3.*
