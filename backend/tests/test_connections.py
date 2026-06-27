"""Tests for C1 — catalog, connections CRUD, OAuth flow, MCP exposer."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tests.conftest import make_connection_row


# ---------------------------------------------------------------------------
# GET /catalog
# ---------------------------------------------------------------------------

class TestCatalog:
    def test_returns_apps_list(self, client):
        res = client.get("/catalog")
        assert res.status_code == 200
        body = res.json()
        assert "apps" in body
        assert len(body["apps"]) > 0

    def test_app_shape(self, client):
        res = client.get("/catalog")
        app = res.json()["apps"][0]
        assert "app" in app
        assert "display_name" in app
        assert "description" in app
        assert "icon" in app

    def test_strava_present(self, client):
        res = client.get("/catalog")
        apps = {a["app"] for a in res.json()["apps"]}
        assert "strava" in apps

    def test_gmail_present(self, client):
        res = client.get("/catalog")
        apps = {a["app"] for a in res.json()["apps"]}
        assert "gmail" in apps


# ---------------------------------------------------------------------------
# GET /connections
# ---------------------------------------------------------------------------

class TestListConnections:
    def test_empty_returns_empty_list(self, client):
        res = client.get("/connections")
        assert res.status_code == 200
        assert res.json() == {"connections": []}

    def test_returns_connections(self, client, mock_db):
        row = make_connection_row()
        mock_db.table.return_value.execute.return_value = MagicMock(data=[row])

        res = client.get("/connections")
        assert res.status_code == 200
        conns = res.json()["connections"]
        assert len(conns) == 1
        assert conns[0]["app"] == "strava"
        assert conns[0]["status"] == "connected"

    def test_connection_has_mcp_url(self, client, mock_db):
        row = make_connection_row(mcp_url="http://localhost:9000/mcp/strava")
        mock_db.table.return_value.execute.return_value = MagicMock(data=[row])

        res = client.get("/connections")
        conn = res.json()["connections"][0]
        assert conn["mcp_url"] == "http://localhost:9000/mcp/strava"

    def test_connection_has_available_tools(self, client, mock_db):
        row = make_connection_row(available_tools=["get_activities", "get_athlete"])
        mock_db.table.return_value.execute.return_value = MagicMock(data=[row])

        res = client.get("/connections")
        conn = res.json()["connections"][0]
        assert "get_activities" in conn["available_tools"]


# ---------------------------------------------------------------------------
# POST /connections  — mock mode (no COMPOSIO_API_KEY)
# ---------------------------------------------------------------------------

class TestConnectApp:
    def test_connect_strava_mock_mode(self, client, mock_db):
        row = make_connection_row(app="strava")
        mock_db.table.return_value.execute.return_value = MagicMock(data=[row])

        res = client.post("/connections", json={"app": "strava"})
        assert res.status_code == 200
        body = res.json()
        assert body["connection"]["app"] == "strava"
        # In mock mode there is no OAuth redirect
        assert body["redirect_url"] is None

    def test_connect_activates_immediately_in_mock_mode(self, client, mock_db):
        row = make_connection_row(app="gmail", status="connected")
        mock_db.table.return_value.execute.return_value = MagicMock(data=[row])

        res = client.post("/connections", json={"app": "gmail"})
        assert res.status_code == 200
        assert res.json()["connection"]["status"] == "connected"

    def test_connect_returns_tools_in_mock_mode(self, client, mock_db):
        row = make_connection_row(
            app="strava",
            available_tools=["get_activities", "get_activity_detail", "get_athlete"],
        )
        mock_db.table.return_value.execute.return_value = MagicMock(data=[row])

        res = client.post("/connections", json={"app": "strava"})
        tools = res.json()["connection"]["available_tools"]
        assert len(tools) > 0


# ---------------------------------------------------------------------------
# GET /connections/callback
# ---------------------------------------------------------------------------

class TestCallback:
    def test_callback_unknown_connection_returns_404(self, client, mock_db):
        mock_db.table.return_value.execute.return_value = MagicMock(data=[])

        res = client.get(
            "/connections/callback",
            params={"connection_id": "unknown-id"},
            follow_redirects=False,
        )
        assert res.status_code == 404

    def test_callback_known_connection_redirects(self, client, mock_db):
        row = make_connection_row()
        mock_db.table.return_value.execute.return_value = MagicMock(data=[row])

        res = client.get(
            "/connections/callback",
            params={"connection_id": row["id"]},
            follow_redirects=False,
        )
        assert res.status_code in (302, 307)
        assert "connection_id" in res.headers["location"]


# ---------------------------------------------------------------------------
# composio_client — unit tests (no HTTP calls)
# ---------------------------------------------------------------------------

class TestComposioClientMockMode:
    def test_initiate_returns_mock_account_id(self):
        from app.connections.composio_client import initiate_connection
        result = initiate_connection("strava")
        assert result.account_id.startswith("mock-")
        assert result.redirect_url is None

    def test_get_status_mock_is_connected(self):
        from app.connections.composio_client import get_connection_status
        from app.contracts import ConnectionStatus
        status = get_connection_status("mock-strava-account")
        assert status == ConnectionStatus.CONNECTED

    def test_get_mcp_url_mock(self):
        from app.connections.composio_client import get_mcp_url
        url = get_mcp_url("strava", "mock-strava-account")
        assert "strava" in url

    def test_get_available_tools_mock(self):
        from app.connections.composio_client import get_available_tools
        tools = get_available_tools("strava", "mock-strava-account")
        assert "get_activities" in tools

    def test_get_available_tools_unknown_app(self):
        from app.connections.composio_client import get_available_tools
        tools = get_available_tools("unknown_app", "mock-unknown-account")
        assert tools == []


# ---------------------------------------------------------------------------
# mcp_exposer — unit tests
# ---------------------------------------------------------------------------

class TestMcpExposer:
    def test_get_mcp_block_connected(self):
        from app.connections.mcp_exposer import get_mcp_block
        from app.contracts import Connection, ConnectionStatus

        conn = Connection(
            id="c1",
            user_id="u1",
            app="strava",
            status=ConnectionStatus.CONNECTED,
            mcp_url="http://localhost:9000/mcp/strava",
            available_tools=["get_activities"],
        )
        block = get_mcp_block(conn)
        assert block is not None
        assert block["mcp_url"] == "http://localhost:9000/mcp/strava"
        assert "get_activities" in block["allowed_tools"]

    def test_get_mcp_block_pending_returns_none(self):
        from app.connections.mcp_exposer import get_mcp_block
        from app.contracts import Connection, ConnectionStatus

        conn = Connection(
            id="c2",
            user_id="u1",
            app="strava",
            status=ConnectionStatus.PENDING,
            mcp_url=None,
        )
        assert get_mcp_block(conn) is None

    def test_filter_tools_subset(self):
        from app.connections.mcp_exposer import filter_tools
        from app.contracts import Connection, ConnectionStatus

        conn = Connection(
            id="c3",
            user_id="u1",
            app="strava",
            status=ConnectionStatus.CONNECTED,
            mcp_url="http://localhost:9000/mcp/strava",
            available_tools=["get_activities", "get_athlete", "get_activity_detail"],
        )
        result = filter_tools(conn, ["get_activities", "unknown_tool"])
        assert result == ["get_activities"]

    def test_filter_tools_empty_request_returns_all(self):
        from app.connections.mcp_exposer import filter_tools
        from app.contracts import Connection, ConnectionStatus

        conn = Connection(
            id="c4",
            user_id="u1",
            app="strava",
            status=ConnectionStatus.CONNECTED,
            mcp_url="http://localhost:9000/mcp/strava",
            available_tools=["get_activities", "get_athlete"],
        )
        assert filter_tools(conn, []) == ["get_activities", "get_athlete"]


# ---------------------------------------------------------------------------
# catalog module — unit tests
# ---------------------------------------------------------------------------

class TestCatalogModule:
    def test_get_catalog_returns_list(self):
        from app.control.catalog import get_catalog
        catalog = get_catalog()
        assert len(catalog) >= 3

    def test_get_catalog_item_strava(self):
        from app.control.catalog import get_catalog_item
        item = get_catalog_item("strava")
        assert item is not None
        assert item.app == "strava"

    def test_get_catalog_item_missing(self):
        from app.control.catalog import get_catalog_item
        assert get_catalog_item("nonexistent_app") is None
