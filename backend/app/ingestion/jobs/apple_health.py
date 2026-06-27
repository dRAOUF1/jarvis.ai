"""Apple Health ingestion job — fetch health metrics to seed memory."""

from __future__ import annotations

from app.contracts import Connection
from app.ingestion.jobs._base import call_mcp_tool

_MOCK_DATA = """\
Recent health metrics:
- Average resting heart rate: 58 bpm
- Average daily steps: 9,200
- Average sleep: 7h20 per night
- VO2 max estimate: 48 ml/kg/min
- Active energy average: 520 kcal/day
"""


async def scrape(connection: Connection) -> str:
    """Return a text summary of recent Apple Health data."""
    if not connection.mcp_url or connection.mcp_url.startswith("http://localhost:9000"):
        return _MOCK_DATA

    result = await call_mcp_tool(connection, "get_health_summary", {})
    if not result:
        return _MOCK_DATA

    lines = ["Health summary:"]
    for key, value in result.items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines)
