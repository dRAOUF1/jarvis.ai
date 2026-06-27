"""GET /catalog, GET/POST /connections, GET /connections/callback  (C1)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from supabase import Client

from app.config import settings
from app.contracts import AppCatalogItem, Connection
from app.control.catalog import get_catalog
from app.connections import oauth as oauth_helpers
from app.deps import get_db

router = APIRouter(tags=["connections"])


# ---------------------------------------------------------------------------
# Response schemas (thin wrappers — not frozen contracts)
# ---------------------------------------------------------------------------

class CatalogResponse(BaseModel):
    apps: list[AppCatalogItem]


class ConnectionsResponse(BaseModel):
    connections: list[Connection]


class ConnectRequest(BaseModel):
    app: str


class ConnectResponse(BaseModel):
    connection: Connection
    redirect_url: str | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/catalog", response_model=CatalogResponse)
def list_catalog():
    return CatalogResponse(apps=get_catalog())


@router.get("/connections", response_model=ConnectionsResponse)
def list_connections(db: Client = Depends(get_db)):
    conns = oauth_helpers.list_connections(db, settings.demo_user_id)
    return ConnectionsResponse(connections=conns)


@router.post("/connections", response_model=ConnectResponse)
async def connect_app(body: ConnectRequest, db: Client = Depends(get_db)):
    connection, redirect_url = await oauth_helpers.initiate_connection(
        db, settings.demo_user_id, body.app
    )
    return ConnectResponse(connection=connection, redirect_url=redirect_url)


@router.get("/connections/callback")
async def oauth_callback(connection_id: str, db: Client = Depends(get_db)):
    """Composio redirects here after OAuth. Updates status and MCP URL."""
    try:
        await oauth_helpers.handle_callback(db, connection_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    # Redirect back to the frontend connections page
    return RedirectResponse(
        url=f"http://localhost:3000/project/connections?connection_id={connection_id}"
    )
