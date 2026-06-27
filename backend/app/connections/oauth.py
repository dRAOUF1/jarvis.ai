"""OAuth connection helpers — initiate, callback, and status refresh."""

from __future__ import annotations

import uuid

from supabase import Client

from app.contracts import Connection, ConnectionStatus
from app.connections import composio_client
from app.db import queries


def _row_to_connection(row: dict) -> Connection:
    # DB column is `scopes`; Connection contract field is `available_tools`
    tools = row.get("available_tools") or row.get("scopes") or []
    return Connection(
        id=row["id"],
        user_id=row["user_id"],
        app=row["app"],
        status=ConnectionStatus(row.get("status", "pending")),
        mcp_url=row.get("mcp_url"),
        available_tools=tools,
    )


def list_connections(db: Client, user_id: str) -> list[Connection]:
    rows = queries.get_connections(db, user_id)
    return [_row_to_connection(r) for r in rows]


def initiate_connection(db: Client, user_id: str, app: str) -> tuple[Connection, str | None]:
    """Create a pending connection row and start the Composio OAuth flow.

    Returns (Connection, redirect_url). redirect_url is None in mock/demo mode.
    """
    result = composio_client.initiate_connection(app)

    row = queries.upsert_connection(db, {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "app": app,
        "status": ConnectionStatus.PENDING.value,
        "composio_account_id": result.account_id,
        "mcp_url": None,
        "scopes": [],
    })

    # If mock (no redirect), immediately activate the connection
    if result.redirect_url is None:
        row = _activate(db, row, result.account_id, app)

    return _row_to_connection(row), result.redirect_url


def handle_callback(db: Client, connection_id: str) -> Connection:
    """Called after Composio redirects back — refresh status and MCP URL."""
    row = queries.get_connection(db, connection_id)
    if not row:
        raise ValueError(f"Connection {connection_id} not found")

    account_id = row.get("composio_account_id", "")
    status = composio_client.get_connection_status(account_id)

    if status == ConnectionStatus.CONNECTED:
        row = _activate(db, row, account_id, row["app"])
    else:
        row = queries.upsert_connection(db, {**row, "status": status.value})

    return _row_to_connection(row)


def _activate(db: Client, row: dict, account_id: str, app: str) -> dict:
    mcp_url = composio_client.get_mcp_url(app, account_id)
    tools = composio_client.get_available_tools(app, account_id)
    updated = {
        **row,
        "status": ConnectionStatus.CONNECTED.value,
        "mcp_url": mcp_url,
        "scopes": tools,
    }
    return queries.upsert_connection(db, updated)
