"""App catalog — apps the shaper can recommend. Co-owned with C1."""
from __future__ import annotations

from app.contracts import AppCatalogItem


CATALOG: list[AppCatalogItem] = [
    AppCatalogItem(
        app="strava",
        display_name="Strava",
        description="Track running, cycling, and other athletic activities",
        icon="🏃",
        default_scopes=["read:activities"],
    ),
    AppCatalogItem(
        app="gmail",
        display_name="Gmail",
        description="Read and send emails from your Gmail inbox",
        icon="📧",
        default_scopes=["gmail.readonly", "gmail.send"],
    ),
    AppCatalogItem(
        app="apple_health",
        display_name="Apple Health",
        description="Access health and fitness data including steps, sleep, and heart rate",
        icon="❤️",
        default_scopes=["health.read"],
    ),
    AppCatalogItem(
        app="github",
        display_name="GitHub",
        description="Manage repositories, issues, pull requests, and code",
        icon="🐙",
        default_scopes=["repo", "issues"],
    ),
    AppCatalogItem(
        app="notion",
        display_name="Notion",
        description="Read and write to Notion pages, databases, and notes",
        icon="📝",
        default_scopes=["read_content", "update_content"],
    ),
    AppCatalogItem(
        app="slack",
        display_name="Slack",
        description="Send messages and read channels in your Slack workspace",
        icon="💬",
        default_scopes=["channels:read", "chat:write"],
    ),
    AppCatalogItem(
        app="google_calendar",
        display_name="Google Calendar",
        description="Read and create events on your Google Calendar",
        icon="📅",
        default_scopes=["calendar.readonly", "calendar.events"],
    ),
    AppCatalogItem(
        app="spotify",
        display_name="Spotify",
        description="Control playback, browse playlists, and discover music",
        icon="🎵",
        default_scopes=["user-read-playback-state", "playlist-read-private"],
    ),
]

CATALOG_BY_APP: dict[str, AppCatalogItem] = {item.app: item for item in CATALOG}


def get_catalog() -> list[AppCatalogItem]:
    return CATALOG


def get_catalog_item(app_id: str) -> AppCatalogItem | None:
    return CATALOG_BY_APP.get(app_id)


# Backwards-compat alias used by shaper.py
get_app = get_catalog_item
