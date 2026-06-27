# jarvis.ai — UML & Architecture Diagrams

> All diagrams are Mermaid. They render on GitHub automatically.
> This is the **picture**; `ARCHITECTURE.md` is the **words**; `TEAM_PLAN.md` is the **work**.

The product in one line: a non-technical user talks to a **main agent**, shapes any project by
conversation, and the system compiles that into a real **Hermes profile** wired to the user's real
apps (via **Composio**) with pre-scraped memory — then chats with it. The user can create many
independent projects.

---

## 1. System architecture (components & ownership)

Colors = which team owns the box.
F=Frontend · B1=Control plane · B2=Runtime/Infra · C1=Composio · C2=Hermes wiring/Ingestion.

```mermaid
flowchart TB
    subgraph FE["Frontend — Next.js (F)"]
        direction TB
        SHAPE_UI["Shaping chat\n(main agent)"]
        DASH["Project dashboard"]
        PROV_UI["Provisioning\nprogress view"]
        CONN_UI["Connect apps\n(OAuth toggles)"]
        CHAT_UI["Project chat +\nmemory/actions side panel"]
    end

    subgraph API["Backend — FastAPI"]
        ROUTER["main.py + routers/\nAPI scaffold (B2)"]

        subgraph CTRL["Control plane (B1)"]
            SHAPER["shaper.py\nslot-filling interview"]
            COMPILER["compiler.py\nProjectSpec -> ArtifactBundle"]
            META["meta.py route"]
        end

        subgraph RT["Runtime plane (B2)"]
            RUNTIME["AgentRuntime\nHermes | Mock"]
            PROVISIONER["ProfileProvisioner\n+ state machine"]
        end

        subgraph CONN["Connections (C1)"]
            COMPOSIO["composio_client.py"]
            CATALOG["app catalog"]
            MCPEXP["mcp_exposer.py"]
        end

        subgraph WIRE["Hermes wiring + ingestion (C2)"]
            WRITER["hermes_writer.py\nprofile dir + config.yaml"]
            INGEST["ingestor.py\nper-app scrape -> MEMORY.md"]
        end

        DB["db/ — Supabase client\n+ migrations (B2)"]
    end

    subgraph HERMES["Hermes gateways (C2 + B2) — warm, pinned"]
        GW_A["Profile: project A\nport 8642"]
        GW_B["Profile: project B\nport 8643"]
        POOL["warm spare pool"]
    end

    subgraph EXT["External"]
        COMPOSIO_CLOUD["Composio\n(Strava, Gmail, Apple Health...)"]
        ANTHROPIC["Anthropic API\n(Claude Sonnet 4.6)"]
    end

    PG["(Supabase Postgres)"]

    SHAPE_UI -->|"SSE /projects/shape"| SHAPER
    DASH -->|"REST /projects"| ROUTER
    PROV_UI -->|"poll /projects/:id/status"| PROVISIONER
    CONN_UI -->|"REST /connections"| COMPOSIO
    CHAT_UI -->|"SSE /projects/:id/chat"| RUNTIME

    SHAPER --> COMPILER
    SHAPER --> CATALOG
    SHAPER --> ANTHROPIC
    COMPILER --> ANTHROPIC
    COMPILER --> PROVISIONER

    PROVISIONER --> COMPOSIO
    PROVISIONER --> WRITER
    PROVISIONER --> INGEST
    PROVISIONER --> GW_A
    PROVISIONER --> POOL

    COMPOSIO --> COMPOSIO_CLOUD
    MCPEXP --> COMPOSIO_CLOUD
    WRITER --> GW_A
    INGEST --> GW_A
    INGEST --> ANTHROPIC

    RUNTIME --> GW_A
    RUNTIME --> GW_B
    GW_A -->|"MCP tools"| COMPOSIO_CLOUD
    RUNTIME -.->|"RUNTIME_MODE=mock fallback"| ANTHROPIC

    ROUTER --> DB
    DB --> PG
```

---

## 2. The creation pipeline (sequence) — "dumb prompt → working agent"

This is your exact flow as typed handoffs. Each arrow's payload is a frozen contract object.

```mermaid
sequenceDiagram
    autonumber
    actor U as Non-tech user
    participant F as Frontend
    participant SH as Shaper (B1)
    participant CO as Compiler (B1)
    participant CN as Composio (C1)
    participant PR as Provisioner (B2)
    participant WR as Hermes writer (C2)
    participant IN as Ingestor (C2)
    participant GW as Hermes gateway

    U->>F: "I want a sports coaching thing" (basic)
    F->>SH: SSE /projects/shape (message)
    loop slot-filling interview
        SH-->>F: question / spec_update events
        U->>F: answers
        F->>SH: message
    end
    SH-->>F: proposal event (ProjectSpec + suggested apps)
    U->>F: confirm + pick apps to connect

    F->>CN: POST /connections (app=strava ...)
    CN-->>F: OAuth redirect -> Connection(status=connected, mcp_url)

    F->>CO: POST /projects (ProjectSpec)
    CO->>CO: compile -> ArtifactBundle (SOUL/USER/config + tool_requirements)
    CO->>PR: provision(bundle, connections)

    Note over PR: state machine starts (UI watches /status)
    PR->>WR: write profile dir + config.yaml (MCP blocks from Connections)
    WR->>GW: register MCP, reload
    PR->>GW: warm gateway
    PR->>IN: ingest(project, connections)
    IN->>GW: scrape via tools (bounded, read-only)
    IN->>IN: summarize -> MEMORY.md
    PR-->>F: status = READY (ProfileHandle)

    U->>F: "How was my last run?"
    F->>GW: SSE /projects/:id/chat (via AgentRuntime)
    GW-->>F: delta + action events (streamed)
```

---

## 3. Contracts (class diagram) — the shared spine

These Pydantic models live in `backend/app/contracts/`. **This is the single source of truth.**
The frontend's TypeScript types are auto-generated from these via OpenAPI. Nobody hand-writes types twice.

```mermaid
classDiagram
    class ProjectSpec {
        +str name
        +str goal
        +str persona
        +List~TaskItem~ tasks
        +List~ToolRequirement~ tool_requirements
        +List~str~ success_criteria
        +str avatar_seed
    }
    class TaskItem {
        +str title
        +str description
    }
    class ToolRequirement {
        +str app
        +str reason
        +List~str~ needed_scopes
        +List~str~ tool_subset
    }
    class ArtifactBundle {
        +str soul_md
        +str user_md
        +str memory_md
        +str config_yaml
        +str runtime_key
        +str session_key
        +List~ToolRequirement~ tool_requirements
    }
    class Connection {
        +str id
        +str user_id
        +str app
        +ConnectionStatus status
        +str mcp_url
        +List~str~ available_tools
    }
    class ProfileHandle {
        +str project_id
        +str gateway_url
        +str gateway_key
        +str session_key
        +str runtime_key
        +ProvisioningState status
    }
    class Project {
        +str id
        +str user_id
        +str name
        +str goal
        +ProvisioningState status
        +str failed_stage
        +ProjectSpec spec
        +str avatar_seed
    }
    class RuntimeEvent {
        <<union>>
        delta(text)
        action(label, detail)
        done()
        error(message)
    }
    class ShapingEvent {
        <<union>>
        delta(text)
        question(field, prompt, options)
        spec_update(partial)
        proposal(spec, suggested_apps)
        done()
    }
    class ProvisioningState {
        <<enum>>
        DRAFT
        COMPILING
        CONNECTING
        PROVISIONING
        INGESTING
        READY
        FAILED
    }
    class ConnectionStatus {
        <<enum>>
        PENDING
        CONNECTED
        ERROR
    }

    ProjectSpec "1" *-- "many" TaskItem
    ProjectSpec "1" *-- "many" ToolRequirement
    ArtifactBundle "1" *-- "many" ToolRequirement
    Project "1" --> "1" ProjectSpec
    Project "1" --> "0..1" ProfileHandle
    ArtifactBundle ..> ProjectSpec : compiled from
    ProfileHandle --> ProvisioningState
    Connection --> ConnectionStatus
```

---

## 4. The swap-able engine (class diagram) — the insurance policy

```mermaid
classDiagram
    class AgentRuntime {
        <<interface>>
        +chat(project_id, session_key, session_id, messages) AsyncIterable~RuntimeEvent~
    }
    class HermesRuntime {
        +chat(...) AsyncIterable~RuntimeEvent~
    }
    class MockRuntime {
        -read_memory(project_id)
        -write_memory(project_id, entry)
        +chat(...) AsyncIterable~RuntimeEvent~
    }
    class ProfileProvisioner {
        <<interface>>
        +provision(bundle, connections) ProfileHandle
        +status(project_id) ProvisioningState
    }
    class WarmPoolProvisioner {
        -assign_gateway()
        +provision(...) ProfileHandle
    }
    class ModalProvisioner {
        +provision(...) ProfileHandle
    }

    AgentRuntime <|.. HermesRuntime
    AgentRuntime <|.. MockRuntime
    ProfileProvisioner <|.. WarmPoolProvisioner
    ProfileProvisioner <|.. ModalProvisioner
    note for MockRuntime "RUNTIME_MODE=mock\nflip in <60s on demo morning"
    note for ModalProvisioner "post-hackathon;\ninterface already matches"
```

---

## 5. Provisioning state machine — what the progress UI renders

```mermaid
stateDiagram-v2
    [*] --> DRAFT: spec confirmed
    DRAFT --> COMPILING: POST /projects
    COMPILING --> CONNECTING: bundle valid
    CONNECTING --> PROVISIONING: connections resolved
    PROVISIONING --> INGESTING: profile written + gateway warm
    INGESTING --> READY: memory seeded
    READY --> [*]

    COMPILING --> FAILED: schema invalid
    CONNECTING --> FAILED: OAuth missing
    PROVISIONING --> FAILED: gateway/MCP handshake
    INGESTING --> FAILED: scrape error
    FAILED --> COMPILING: retry from failed stage

    note right of INGESTING
        bounded, read-only,
        time-boxed per app
    end note
```

---

## 6. Where the Hermes repo lives in all this

Hermes is **not** imported as a library and **not** orchestrated over MCP. It runs as **gateway
processes** (one profile per project) that the FastAPI backend talks to over an OpenAI-compatible
REST API. The relationship is one-directional: **Hermes connects out to Composio MCP servers** to
use tools; the backend connects in to Hermes to send chat.

```mermaid
flowchart LR
    BE["FastAPI backend\n(AgentRuntime)"] -->|"POST /v1/chat/completions\n+ X-Hermes-Session-Key"| GW

    subgraph GW["Hermes gateway (per project)"]
        PROFILE["profile dir\nSOUL.md / USER.md / MEMORY.md\nconfig.yaml"]
        APISRV["API_SERVER_ENABLED=true\nbearer key, pinned version"]
    end

    GW -->|"MCP client"| COMP["Composio MCP\n(Strava, Gmail...)"]
    GW -->|"model = Claude Sonnet 4.6"| ANTH["Anthropic"]

    repo["/hermes in monorepo\n= profile templates +\nconfig snippets + run scripts\n(C2 owns)"] -.->|"generates"| PROFILE
```

The `/hermes` folder in the repo holds the **template profile**, **config.yaml snippets**, and
**run/warm scripts**. C2's `hermes_writer.py` stamps a new profile dir from the template at
provision time and fills in MCP blocks from the resolved `Connection` objects.
