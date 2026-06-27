# backend/ — Claude Code local rules

FastAPI + Pydantic v2 + async. Contracts live in `app/contracts/` and are FROZEN — import them,
never redefine. Routers are THIN; logic lives in `control/`, `runtime/`, `provisioning/`,
`connections/`, `ingestion/`. DB via `app/db/`. Build against `app/mocks/*` until the real
dependency lands. AI only in shaping/compilation-freetext/ingestion-summary; provisioning is
deterministic. Session-key convention is frozen (root `ARCHITECTURE.md §7`). See `TEAM_PLAN.md` for
your section.
