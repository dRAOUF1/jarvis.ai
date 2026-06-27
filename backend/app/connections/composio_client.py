"""Composio v3 REST API wrapper.

Falls back to mock data when COMPOSIO_API_KEY is not set, so the demo
works without a real Composio account.

v3 endpoints used:
  GET  /api/v3/auth_configs             — list auth configs (app→auth_config_id)
  POST /api/v3/connected_accounts/link  — initiate OAuth → redirect URL
  GET  /api/v3/connected_accounts/{id}  — poll status
  GET  /api/v3/toolkits/{slug}/tools    — list available tools
"""

from __future__ import annotations

import httpx

from app.config import settings
from app.contracts import ConnectionStatus

_BASE = "https://backend.composio.dev/api/v3"

# Tools available per app in mock mode
_MOCK_TOOLS: dict[str, list[str]] = {
    "strava": ["get_activities", "get_activity_detail", "get_athlete"],
    "gmail": ["list_emails", "read_email", "send_email", "search_emails"],
    "google_calendar": ["list_events", "create_event", "get_event"],
    "github": ["list_repos", "list_issues", "create_issue", "get_pull_request"],
    "notion": ["search_pages", "read_page", "create_page"],
    "slack": ["list_channels", "send_message", "read_channel"],
}

_MOCK_MCP_PATTERN = "http://localhost:9000/mcp/{app}"

# Cache: app slug → auth_config_id (populated lazily)
_AUTH_CONFIG_CACHE: dict[str, str] = {}


def _has_real_key() -> bool:
    return bool(settings.composio_api_key)


def _headers() -> dict[str, str]:
    return {"x-api-key": settings.composio_api_key, "Content-Type": "application/json"}


def _get_auth_config_id(app: str) -> str | None:
    """Return the Composio auth_config_id for an app, using a lazy cache."""
    if app in _AUTH_CONFIG_CACHE:
        return _AUTH_CONFIG_CACHE[app]

    try:
        with httpx.Client(timeout=10) as client:
            res = client.get(f"{_BASE}/auth_configs?limit=50", headers=_headers())
            res.raise_for_status()
            for item in res.json().get("items", []):
                slug = item.get("toolkit", {}).get("slug", "")
                _AUTH_CONFIG_CACHE[slug] = item["id"]
    except (httpx.RequestError, httpx.HTTPStatusError, KeyError):
        pass

    return _AUTH_CONFIG_CACHE.get(app)


class ComposioInitResult:
    def __init__(self, account_id: str, redirect_url: str | None):
        self.account_id = account_id
        self.redirect_url = redirect_url


def initiate_connection(app: str) -> ComposioInitResult:
    """Start a Composio OAuth flow. Returns account_id + redirect URL."""
    if not _has_real_key():
        return ComposioInitResult(
            account_id=f"mock-{app}-account",
            redirect_url=None,
        )

    auth_config_id = _get_auth_config_id(app)
    if not auth_config_id:
        # No auth config exists for this app — fall back to mock
        return ComposioInitResult(
            account_id=f"mock-{app}-account",
            redirect_url=None,
        )

    with httpx.Client(timeout=10) as client:
        res = client.post(
            f"{_BASE}/connected_accounts/link",
            headers=_headers(),
            json={"auth_config_id": auth_config_id, "user_id": settings.demo_user_id},
        )
        res.raise_for_status()
        data = res.json()
        return ComposioInitResult(
            account_id=data["connected_account_id"],
            redirect_url=data.get("redirect_url"),
        )


def get_connection_status(account_id: str) -> ConnectionStatus:
    """Poll whether a Composio connected account is active."""
    if account_id.startswith("mock-"):
        return ConnectionStatus.CONNECTED

    if not _has_real_key():
        return ConnectionStatus.CONNECTED

    try:
        with httpx.Client(timeout=10) as client:
            res = client.get(
                f"{_BASE}/connected_accounts/{account_id}",
                headers=_headers(),
            )
            if res.status_code == 404:
                return ConnectionStatus.ERROR
            res.raise_for_status()
            status = res.json().get("status", "")
            if status == "ACTIVE":
                return ConnectionStatus.CONNECTED
            if status in ("FAILED", "EXPIRED", "DISABLED"):
                return ConnectionStatus.ERROR
            return ConnectionStatus.PENDING
    except (httpx.RequestError, httpx.HTTPStatusError):
        return ConnectionStatus.ERROR


def get_mcp_url(app: str, account_id: str) -> str:
    """Return the MCP server URL for a connected account."""
    if account_id.startswith("mock-") or not _has_real_key():
        return _MOCK_MCP_PATTERN.format(app=app)
    # Composio MCP URL pattern (v3)
    return f"https://mcp.composio.dev/{app}?api_key={settings.composio_api_key}&connected_account_id={account_id}"


def get_available_tools(app: str, account_id: str) -> list[str]:
    """Return the tool list for a connected app."""
    if account_id.startswith("mock-") or not _has_real_key():
        return _MOCK_TOOLS.get(app, [])

    try:
        with httpx.Client(timeout=10) as client:
            res = client.get(
                f"{_BASE}/toolkits/{app}/tools?limit=50",
                headers=_headers(),
            )
            res.raise_for_status()
            items = res.json().get("items", [])
            return [item["slug"] for item in items if item.get("slug")]
    except (httpx.RequestError, httpx.HTTPStatusError):
        return _MOCK_TOOLS.get(app, [])
