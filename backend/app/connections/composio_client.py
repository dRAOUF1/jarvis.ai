"""Composio v3 REST API wrapper (async).

Falls back to mock data gracefully when:
  - COMPOSIO_API_KEY is not set
  - No auth config exists for the requested app (e.g. Strava not yet configured)
  - Any Composio API call fails (read-only key, network error, etc.)

Composio v3 endpoints used:
  GET  /api/v3/auth_configs                    — list auth configs (app → auth_config_id)
  POST /api/v3/connected_accounts/link         — initiate OAuth → redirect URL
  GET  /api/v3/connected_accounts/{id}         — poll connection status
  GET  /api/v3/tools?toolkit={slug}&limit=50   — list available tools for an app

Dashboard setup required for each app before real OAuth works:
  1. Log into app.composio.dev
  2. Create an auth config for each app (strava, gmail, apple_health, etc.)
  3. Ensure the API key in .env has write permissions (current key is read-only)

MCP URL note: the mcp.composio.dev URL is only consumed by the Hermes gateway
in RUNTIME_MODE=hermes. In mock mode it is never called. Verify the URL format
when Hermes gateways are provisioned.
"""

from __future__ import annotations

import httpx

from app.config import settings
from app.contracts import ConnectionStatus

_BASE = "https://backend.composio.dev/api/v3"

# Fallback tool lists used when the real Composio API is unavailable or returns
# no results. Slugs match the Composio tool naming convention (UPPERCASE_SNAKE).
_MOCK_TOOLS: dict[str, list[str]] = {
    "strava": [
        "STRAVA_GET_ATHLETE",
        "STRAVA_LIST_ATHLETE_ACTIVITIES",
        "STRAVA_GET_ACTIVITY",
        "STRAVA_GET_ATHLETE_STATS",
    ],
    "gmail": [
        "GMAIL_LIST_MESSAGES",
        "GMAIL_GET_MESSAGE",
        "GMAIL_SEND_EMAIL",
        "GMAIL_SEARCH_EMAILS",
        "GMAIL_CREATE_DRAFT",
    ],
    "googlecalendar": [
        "GOOGLECALENDAR_LIST_EVENTS",
        "GOOGLECALENDAR_CREATE_EVENT",
        "GOOGLECALENDAR_GET_EVENT",
        "GOOGLECALENDAR_UPDATE_EVENT",
    ],
    "apple_health": [
        "APPLEHEALTH_GET_STEPS",
        "APPLEHEALTH_GET_HEART_RATE",
        "APPLEHEALTH_GET_SLEEP",
        "APPLEHEALTH_GET_WORKOUTS",
    ],
    "github": [
        "GITHUB_LIST_REPOS",
        "GITHUB_LIST_ISSUES",
        "GITHUB_CREATE_ISSUE",
        "GITHUB_GET_PULL_REQUEST",
        "GITHUB_LIST_PULL_REQUESTS",
    ],
    "notion": [
        "NOTION_SEARCH",
        "NOTION_GET_PAGE",
        "NOTION_CREATE_PAGE",
        "NOTION_UPDATE_PAGE",
        "NOTION_QUERY_DATABASE",
    ],
    "slack": [
        "SLACK_LIST_CHANNELS",
        "SLACK_SEND_MESSAGE",
        "SLACK_GET_MESSAGES",
        "SLACK_LIST_USERS",
    ],
    "spotify": [
        "SPOTIFY_GET_CURRENT_TRACK",
        "SPOTIFY_GET_PLAYLISTS",
        "SPOTIFY_SEARCH_TRACKS",
        "SPOTIFY_CONTROL_PLAYBACK",
    ],
}

# Composio MCP URL pattern — only used by Hermes gateway in runtime=hermes mode.
_MCP_URL_PATTERN = (
    "https://mcp.composio.dev/{app}"
    "?api_key={api_key}&connected_account_id={account_id}"
)
_MOCK_MCP_PATTERN = "http://localhost:9000/mcp/{app}"

# Lazy cache: app slug → auth_config_id
_AUTH_CONFIG_CACHE: dict[str, str] = {}


def _has_real_key() -> bool:
    return bool(settings.composio_api_key)


def _headers() -> dict[str, str]:
    return {
        "x-api-key": settings.composio_api_key,
        "Content-Type": "application/json",
    }


async def _get_auth_config_id(app: str) -> str | None:
    """Return the Composio auth_config_id for an app, using a lazy cache."""
    if app in _AUTH_CONFIG_CACHE:
        return _AUTH_CONFIG_CACHE[app]

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(
                f"{_BASE}/auth_configs?limit=50", headers=_headers()
            )
            res.raise_for_status()
            for item in res.json().get("items", []):
                slug = item.get("toolkit", {}).get("slug", "")
                if slug:
                    _AUTH_CONFIG_CACHE[slug] = item["id"]
    except (httpx.RequestError, httpx.HTTPStatusError, KeyError):
        pass

    return _AUTH_CONFIG_CACHE.get(app)


class ComposioInitResult:
    def __init__(self, account_id: str, redirect_url: str | None):
        self.account_id = account_id
        self.redirect_url = redirect_url


async def initiate_connection(app: str) -> ComposioInitResult:
    """Start a Composio OAuth flow. Returns account_id + redirect URL.

    Falls back to mock (no redirect, instant activation) if:
    - No API key configured
    - No auth config exists for the app in Composio
    - The API call fails (read-only key, network error, etc.)
    """
    if not _has_real_key():
        return ComposioInitResult(
            account_id=f"mock-{app}-account",
            redirect_url=None,
        )

    auth_config_id = await _get_auth_config_id(app)
    if not auth_config_id:
        # No auth config in Composio for this app — needs dashboard setup.
        return ComposioInitResult(
            account_id=f"mock-{app}-account",
            redirect_url=None,
        )

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.post(
                f"{_BASE}/connected_accounts/link",
                headers=_headers(),
                json={
                    "auth_config_id": auth_config_id,
                    "user_id": settings.demo_user_id,
                },
            )
            res.raise_for_status()
            data = res.json()
            return ComposioInitResult(
                account_id=data["connected_account_id"],
                redirect_url=data.get("redirect_url"),
            )
    except (httpx.RequestError, httpx.HTTPStatusError, KeyError):
        # API key may lack write permissions — fall back to mock gracefully.
        return ComposioInitResult(
            account_id=f"mock-{app}-account",
            redirect_url=None,
        )


async def get_connection_status(account_id: str) -> ConnectionStatus:
    """Poll whether a Composio connected account is active."""
    if account_id.startswith("mock-"):
        return ConnectionStatus.CONNECTED

    if not _has_real_key():
        return ConnectionStatus.CONNECTED

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(
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
    """Return the MCP server URL for a connected account.

    Only used by the Hermes gateway (RUNTIME_MODE=hermes).
    In mock mode this URL is never called.
    """
    if account_id.startswith("mock-") or not _has_real_key():
        return _MOCK_MCP_PATTERN.format(app=app)
    return _MCP_URL_PATTERN.format(
        app=app,
        api_key=settings.composio_api_key,
        account_id=account_id,
    )


async def get_available_tools(app: str, account_id: str) -> list[str]:
    """Return the tool list for a connected app.

    Attempts to fetch the live tool list from Composio; falls back to
    _MOCK_TOOLS on any error (including filter issues with the v3 API).
    """
    if account_id.startswith("mock-") or not _has_real_key():
        return _MOCK_TOOLS.get(app, [])

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(
                f"{_BASE}/tools?toolkit={app}&limit=50",
                headers=_headers(),
            )
            res.raise_for_status()
            items = res.json().get("items", [])
            # Filter to only tools belonging to this app (toolkit param may not
            # filter server-side in all API versions).
            prefix = app.upper() + "_"
            app_tools = [
                item["slug"]
                for item in items
                if item.get("slug", "").startswith(prefix)
            ]
            return app_tools if app_tools else _MOCK_TOOLS.get(app, [])
    except (httpx.RequestError, httpx.HTTPStatusError):
        return _MOCK_TOOLS.get(app, [])
