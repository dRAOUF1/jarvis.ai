"""Base MCP scraping helper shared by all ingestion jobs."""

from __future__ import annotations

import json
import httpx

from app.contracts import Connection


async def call_mcp_tool(
    connection: Connection,
    tool_name: str,
    arguments: dict | None = None,
    *,
    timeout: float = 10.0,
) -> dict:
    """Call a single MCP tool via JSON-RPC 2.0 and return the result dict.

    Returns an empty dict on connection errors so scraping never crashes
    provisioning.
    """
    if not connection.mcp_url:
        return {}

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments or {}},
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            res = await client.post(
                connection.mcp_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            res.raise_for_status()
            data = res.json()
            return data.get("result", {})
    except (httpx.RequestError, httpx.HTTPStatusError, json.JSONDecodeError):
        return {}
