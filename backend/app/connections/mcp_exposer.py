"""Derive MCP URL and scoped tool list from a Connection.

Used by the provisioner when wiring a project's MCP block.
"""

from __future__ import annotations

from app.contracts import Connection, ConnectionStatus


def get_mcp_block(connection: Connection) -> dict | None:
    """Return an MCP config dict for a connected app, or None if not ready."""
    if connection.status != ConnectionStatus.CONNECTED or not connection.mcp_url:
        return None
    return {
        "app": connection.app,
        "mcp_url": connection.mcp_url,
        "allowed_tools": connection.available_tools,
    }


def filter_tools(connection: Connection, requested: list[str]) -> list[str]:
    """Intersect requested tools with what the connection actually provides."""
    if not requested:
        return connection.available_tools
    available = set(connection.available_tools)
    return [t for t in requested if t in available]
