"""Strava ingestion job — fetch recent activities for seeding memory."""

from __future__ import annotations

import json

from app.contracts import Connection
from app.ingestion.jobs._base import call_mcp_tool

# Max activities to fetch on first ingest (keep it bounded)
_ACTIVITY_LIMIT = 10

_MOCK_DATA = """\
Recent activities:
- Run: 5.2 km in 26 min (pace 5:00/km) — 2 days ago
- Run: 10.1 km in 52 min (pace 5:09/km) — 5 days ago
- Ride: 32 km in 1h10 — 8 days ago
- Run: 5.0 km in 25 min (pace 5:00/km) — 11 days ago
Weekly mileage average: ~22 km
"""


async def scrape(connection: Connection) -> str:
    """Return a text summary of recent Strava activities."""
    if not connection.mcp_url or connection.mcp_url.startswith("http://localhost:9000"):
        return _MOCK_DATA

    result = await call_mcp_tool(
        connection,
        "get_activities",
        {"limit": _ACTIVITY_LIMIT},
    )
    if not result:
        return _MOCK_DATA

    activities = result.get("activities", result) if isinstance(result, dict) else result
    lines = ["Recent Strava activities:"]
    for act in activities[:_ACTIVITY_LIMIT]:
        if isinstance(act, dict):
            name = act.get("name", "Activity")
            dist = act.get("distance", 0)
            elapsed = act.get("elapsed_time", 0)
            lines.append(f"- {name}: {dist/1000:.1f} km in {elapsed//60} min")
    return "\n".join(lines)
