"""App catalog — apps the shaper can recommend. Co-owned with C1."""
from __future__ import annotations

from pydantic import BaseModel


class AppCatalogItem(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    default_tool_subset: list[str]
    default_scopes: list[str]


CATALOG: list[AppCatalogItem] = [
    AppCatalogItem(
        id="strava",
        name="Strava",
        description="Track running, cycling, and other athletic activities",
        icon="🏃",
        default_tool_subset=["get_activities", "get_activity_detail", "get_athlete_stats"],
        default_scopes=["read:activities"],
    ),
    AppCatalogItem(
        id="gmail",
        name="Gmail",
        description="Read and send emails from your Gmail inbox",
        icon="📧",
        default_tool_subset=["list_messages", "get_message", "send_email", "search_emails"],
        default_scopes=["gmail.readonly", "gmail.send"],
    ),
    AppCatalogItem(
        id="apple_health",
        name="Apple Health",
        description="Access health and fitness data including steps, sleep, and heart rate",
        icon="❤️",
        default_tool_subset=["get_steps", "get_heart_rate", "get_sleep", "get_workouts"],
        default_scopes=["health.read"],
    ),
    AppCatalogItem(
        id="github",
        name="GitHub",
        description="Manage repositories, issues, pull requests, and code",
        icon="🐙",
        default_tool_subset=["list_repos", "get_issues", "create_issue", "list_prs", "get_pr"],
        default_scopes=["repo", "issues"],
    ),
    AppCatalogItem(
        id="notion",
        name="Notion",
        description="Read and write to Notion pages, databases, and notes",
        icon="📝",
        default_tool_subset=["search", "get_page", "create_page", "update_page", "query_database"],
        default_scopes=["read_content", "update_content"],
    ),
    AppCatalogItem(
        id="slack",
        name="Slack",
        description="Send messages and read channels in your Slack workspace",
        icon="💬",
        default_tool_subset=["list_channels", "send_message", "get_messages", "list_users"],
        default_scopes=["channels:read", "chat:write"],
    ),
    AppCatalogItem(
        id="google_calendar",
        name="Google Calendar",
        description="Read and create events on your Google Calendar",
        icon="📅",
        default_tool_subset=["list_events", "create_event", "get_event", "update_event"],
        default_scopes=["calendar.readonly", "calendar.events"],
    ),
    AppCatalogItem(
        id="spotify",
        name="Spotify",
        description="Control playback, browse playlists, and discover music",
        icon="🎵",
        default_tool_subset=["get_current_track", "get_playlists", "search_tracks", "control_playback"],
        default_scopes=["user-read-playback-state", "playlist-read-private"],
    ),
]

CATALOG_BY_ID: dict[str, AppCatalogItem] = {app.id: app for app in CATALOG}


def get_catalog() -> list[AppCatalogItem]:
    return CATALOG


def get_app(app_id: str) -> AppCatalogItem | None:
    return CATALOG_BY_ID.get(app_id)
