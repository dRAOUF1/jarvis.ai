"""Shared pytest fixtures for the backend test suite."""

from __future__ import annotations

import os
import uuid
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

# Set required env vars BEFORE importing the app
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
os.environ.setdefault("COMPOSIO_API_KEY", "")  # empty → mock mode


@pytest.fixture()
def mock_db():
    """A mock Supabase client that returns empty data by default."""
    db = MagicMock()
    # Default: tables return empty lists
    _table = MagicMock()
    _table.select.return_value = _table
    _table.insert.return_value = _table
    _table.upsert.return_value = _table
    _table.update.return_value = _table
    _table.eq.return_value = _table
    _table.order.return_value = _table
    _table.execute.return_value = MagicMock(data=[])
    db.table.return_value = _table
    return db


@pytest.fixture()
def client(mock_db):
    """TestClient with the DB dependency overridden."""
    from app.main import app
    from app.deps import get_db

    app.dependency_overrides[get_db] = lambda: mock_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def make_connection_row(
    app: str = "strava",
    status: str = "connected",
    mcp_url: str | None = "http://localhost:9000/mcp/strava",
    available_tools: list[str] | None = None,
) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "user_id": "demo-user",
        "app": app,
        "status": status,
        "mcp_url": mcp_url,
        "available_tools": available_tools or ["get_activities"],
        "composio_account_id": f"mock-{app}-account",
    }
