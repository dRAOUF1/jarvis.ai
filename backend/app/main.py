"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title="jarvis.ai", version="0.1.0")

    # CORS — allow Next.js dev server
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers (stubs filled by each team member)
    from app.routers import projects, chat, provisioning, shaping, meta, connections
    app.include_router(projects.router)
    app.include_router(chat.router)
    app.include_router(provisioning.router)
    app.include_router(shaping.router)
    app.include_router(meta.router)
    app.include_router(connections.router)

    @app.get("/health")
    def health():
        return {"status": "ok", "runtime_mode": settings.runtime_mode}

    return app


app = create_app()
