"""Mock connections — hardcoded Strava connection for the sports demo."""

from __future__ import annotations

from app.contracts import Connection, ConnectionStatus


def get_mock_connections() -> list[Connection]:
    """Return mock Strava connection for the sports coach demo."""
    return [
        Connection(
            id="mock-conn-strava",
            user_id="demo-user",
            app="strava",
            status=ConnectionStatus.CONNECTED,
            mcp_url="http://localhost:9000/mcp/strava",
            available_tools=["get_activities", "get_activity_detail"],
        ),
    ]
