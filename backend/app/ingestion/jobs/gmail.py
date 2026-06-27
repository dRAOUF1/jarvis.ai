"""Gmail ingestion job — fetch recent email subjects to seed user context."""

from __future__ import annotations

from app.contracts import Connection
from app.ingestion.jobs._base import call_mcp_tool

_EMAIL_LIMIT = 20

_MOCK_DATA = """\
Recent email activity:
- Mostly receives newsletters and work updates
- Several fitness-related newsletters (running tips, race registrations)
- Active correspondence with running club
- Inbox has ~200 unread emails
"""


async def scrape(connection: Connection) -> str:
    """Return a text summary of recent Gmail activity."""
    if not connection.mcp_url or connection.mcp_url.startswith("http://localhost:9000"):
        return _MOCK_DATA

    result = await call_mcp_tool(
        connection,
        "list_emails",
        {"max_results": _EMAIL_LIMIT},
    )
    if not result:
        return _MOCK_DATA

    emails = result.get("emails", result) if isinstance(result, dict) else result
    lines = ["Recent emails:"]
    for email in emails[:_EMAIL_LIMIT]:
        if isinstance(email, dict):
            subject = email.get("subject", "(no subject)")
            sender = email.get("from", "unknown")
            lines.append(f"- From {sender}: {subject}")
    return "\n".join(lines)
