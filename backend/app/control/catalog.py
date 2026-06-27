"""Static app catalog — shared by C1 router and B1 compiler."""

from __future__ import annotations

from app.contracts import AppCatalogItem

CATALOG: list[AppCatalogItem] = [
    AppCatalogItem(
        app="strava",
        display_name="Strava",
        description="Running, cycling, and fitness activities",
        icon="🏃",
        default_scopes=["activity:read_all"],
    ),
    AppCatalogItem(
        app="gmail",
        display_name="Gmail",
        description="Read and send emails",
        icon="📧",
        default_scopes=["gmail.readonly", "gmail.send"],
    ),
    AppCatalogItem(
        app="google_calendar",
        display_name="Google Calendar",
        description="Read and create calendar events",
        icon="📅",
        default_scopes=["calendar.readonly", "calendar.events"],
    ),
    AppCatalogItem(
        app="github",
        display_name="GitHub",
        description="Repos, issues, and pull requests",
        icon="🐙",
        default_scopes=["repo", "read:user"],
    ),
    AppCatalogItem(
        app="notion",
        display_name="Notion",
        description="Databases, pages, and docs",
        icon="📝",
        default_scopes=["read_content", "update_content"],
    ),
    AppCatalogItem(
        app="slack",
        display_name="Slack",
        description="Messages and channels",
        icon="💬",
        default_scopes=["channels:read", "chat:write"],
    ),
]

_CATALOG_INDEX: dict[str, AppCatalogItem] = {item.app: item for item in CATALOG}


def get_catalog() -> list[AppCatalogItem]:
    return CATALOG


def get_catalog_item(app: str) -> AppCatalogItem | None:
    return _CATALOG_INDEX.get(app)
