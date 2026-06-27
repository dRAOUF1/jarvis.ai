"""Tests for C2 — HermesWriter, Ingestor, Summarizer, ingestion jobs, state machine."""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Required env vars set before any app import
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
os.environ.setdefault("COMPOSIO_API_KEY", "")

from app.contracts import (
    ArtifactBundle,
    Connection,
    ConnectionStatus,
    ProfileHandle,
    ProvisioningState,
    ToolRequirement,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_bundle(project_id: str = "proj-123", user_id: str = "user-1") -> ArtifactBundle:
    return ArtifactBundle(
        soul_md="You are a sports coach AI.",
        user_md="User is an amateur runner.",
        memory_md="- Fact: User ran 5km yesterday.",
        config_yaml="model: claude-sonnet-4-6\ntemperature: 0.7\n",
        runtime_key="slot-a",
        session_key=f"agent:{project_id}:user:{user_id}",
        tool_requirements=[
            ToolRequirement(app="strava", reason="track runs", needed_scopes=[], tool_subset=[]),
        ],
    )


def _make_connection(
    app: str = "strava",
    status: ConnectionStatus = ConnectionStatus.CONNECTED,
    mcp_url: str = "http://localhost:9000/mcp/strava",
    tools: list[str] | None = None,
) -> Connection:
    return Connection(
        id=str(uuid.uuid4()),
        user_id="user-1",
        app=app,
        status=status,
        mcp_url=mcp_url,
        available_tools=tools or ["get_activities", "get_activity_detail"],
    )


# ---------------------------------------------------------------------------
# HermesWriter
# ---------------------------------------------------------------------------

class TestHermesWriter:
    @pytest.fixture()
    def writer(self, tmp_path):
        from app.provisioning.hermes_writer import HermesWriter
        return HermesWriter(profiles_dir=tmp_path)

    @pytest.mark.asyncio
    async def test_creates_profile_directory(self, writer, tmp_path):
        bundle = _make_bundle("test-proj")
        await writer.write(bundle, [])
        assert (tmp_path / "test-proj").is_dir()

    @pytest.mark.asyncio
    async def test_writes_soul_md(self, writer, tmp_path):
        bundle = _make_bundle("test-proj")
        await writer.write(bundle, [])
        content = (tmp_path / "test-proj" / "SOUL.md").read_text()
        assert "sports coach" in content

    @pytest.mark.asyncio
    async def test_writes_user_md(self, writer, tmp_path):
        bundle = _make_bundle("test-proj")
        await writer.write(bundle, [])
        content = (tmp_path / "test-proj" / "USER.md").read_text()
        assert "amateur runner" in content

    @pytest.mark.asyncio
    async def test_writes_memory_md(self, writer, tmp_path):
        bundle = _make_bundle("test-proj")
        await writer.write(bundle, [])
        content = (tmp_path / "test-proj" / "MEMORY.md").read_text()
        assert "5km" in content

    @pytest.mark.asyncio
    async def test_writes_config_yaml(self, writer, tmp_path):
        bundle = _make_bundle("test-proj")
        await writer.write(bundle, [])
        content = (tmp_path / "test-proj" / "config.yaml").read_text()
        assert "claude-sonnet-4-6" in content

    @pytest.mark.asyncio
    async def test_config_includes_mcp_block_for_connected_app(self, writer, tmp_path):
        bundle = _make_bundle("test-proj")
        conn = _make_connection("strava")
        await writer.write(bundle, [conn])
        content = (tmp_path / "test-proj" / "config.yaml").read_text()
        assert "mcp_servers" in content
        assert "strava" in content
        assert "localhost:9000" in content

    @pytest.mark.asyncio
    async def test_config_excludes_pending_connections(self, writer, tmp_path):
        bundle = _make_bundle("test-proj")
        conn = _make_connection("strava", status=ConnectionStatus.PENDING, mcp_url=None)
        await writer.write(bundle, [conn])
        content = (tmp_path / "test-proj" / "config.yaml").read_text()
        assert "mcp_servers" not in content

    @pytest.mark.asyncio
    async def test_returns_profile_handle(self, writer):
        bundle = _make_bundle("test-proj")
        handle = await writer.write(bundle, [])
        assert isinstance(handle, ProfileHandle)
        assert handle.project_id == "test-proj"
        assert handle.session_key == bundle.session_key
        assert handle.runtime_key == bundle.runtime_key

    @pytest.mark.asyncio
    async def test_uses_gateway_registry_slot(self, tmp_path):
        from app.provisioning.hermes_writer import HermesWriter
        mock_registry = MagicMock()
        mock_slot = MagicMock()
        mock_slot.url = "https://hermes.example.com/v1"
        mock_slot.key = "real-key-123"
        mock_registry.assign.return_value = mock_slot

        writer = HermesWriter(profiles_dir=tmp_path, gateway_registry=mock_registry)
        bundle = _make_bundle("test-proj")
        handle = await writer.write(bundle, [])

        assert handle.gateway_url == "https://hermes.example.com/v1"
        assert handle.gateway_key == "real-key-123"

    @pytest.mark.asyncio
    async def test_falls_back_gracefully_when_no_gateway_slots(self, tmp_path):
        from app.provisioning.hermes_writer import HermesWriter
        mock_registry = MagicMock()
        mock_registry.assign.side_effect = RuntimeError("No warm gateway slots available")

        writer = HermesWriter(profiles_dir=tmp_path, gateway_registry=mock_registry)
        bundle = _make_bundle("test-proj")
        handle = await writer.write(bundle, [])  # must not raise
        assert handle.gateway_url == "http://localhost:8080"

    @pytest.mark.asyncio
    async def test_overwrites_existing_profile(self, writer, tmp_path):
        bundle = _make_bundle("test-proj")
        await writer.write(bundle, [])

        updated = bundle.model_copy(update={"soul_md": "Updated soul content."})
        await writer.write(updated, [])

        content = (tmp_path / "test-proj" / "SOUL.md").read_text()
        assert "Updated soul content." in content

    @pytest.mark.asyncio
    async def test_multiple_connections_in_mcp_block(self, writer, tmp_path):
        bundle = _make_bundle("test-proj")
        conn1 = _make_connection("strava", tools=["get_activities"])
        conn2 = _make_connection("gmail", mcp_url="http://localhost:9000/mcp/gmail", tools=["list_emails"])
        await writer.write(bundle, [conn1, conn2])
        content = (tmp_path / "test-proj" / "config.yaml").read_text()
        assert "strava" in content
        assert "gmail" in content


# ---------------------------------------------------------------------------
# _parse_project_id
# ---------------------------------------------------------------------------

class TestParseProjectId:
    def test_valid_session_key(self):
        from app.provisioning.hermes_writer import _parse_project_id
        assert _parse_project_id("agent:proj-abc:user:user-1") == "proj-abc"

    def test_uuid_project_id(self):
        from app.provisioning.hermes_writer import _parse_project_id
        uid = str(uuid.uuid4())
        assert _parse_project_id(f"agent:{uid}:user:user-1") == uid

    def test_invalid_raises(self):
        from app.provisioning.hermes_writer import _parse_project_id
        with pytest.raises(ValueError):
            _parse_project_id("bad-key-format")


# ---------------------------------------------------------------------------
# Summarizer
# ---------------------------------------------------------------------------

class TestSummarizer:
    @pytest.mark.asyncio
    async def test_empty_input_returns_empty(self):
        from app.ingestion.summarizer import Summarizer
        s = Summarizer()
        result = await s.summarize("", "strava")
        assert result == []

    @pytest.mark.asyncio
    async def test_whitespace_only_returns_empty(self):
        from app.ingestion.summarizer import Summarizer
        s = Summarizer()
        result = await s.summarize("   \n  ", "strava")
        assert result == []

    @pytest.mark.asyncio
    async def test_calls_anthropic_and_returns_bullets(self):
        from app.ingestion.summarizer import Summarizer

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="- User runs 5km regularly\n- Average pace 5 min/km")]
        mock_client.messages.create.return_value = mock_response

        s = Summarizer(client=mock_client)
        result = await s.summarize("5km run in 25 mins", "strava")

        assert len(result) == 2
        assert result[0] == "- User runs 5km regularly"
        assert result[1] == "- Average pace 5 min/km"

    @pytest.mark.asyncio
    async def test_filters_non_bullet_lines(self):
        from app.ingestion.summarizer import Summarizer

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(
            text="Here are the facts:\n- User runs 5km\nSome other text\n- Active weekly"
        )]
        mock_client.messages.create.return_value = mock_response

        s = Summarizer(client=mock_client)
        result = await s.summarize("data", "strava")
        assert len(result) == 2
        assert all(r.startswith("- ") for r in result)

    @pytest.mark.asyncio
    async def test_uses_haiku_model(self):
        from app.ingestion.summarizer import Summarizer

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="- fact")]
        mock_client.messages.create.return_value = mock_response

        s = Summarizer(client=mock_client)
        await s.summarize("some data", "strava")

        call_kwargs = mock_client.messages.create.call_args[1]
        assert "haiku" in call_kwargs["model"]


# ---------------------------------------------------------------------------
# Ingestion jobs
# ---------------------------------------------------------------------------

class TestStravaJob:
    @pytest.mark.asyncio
    async def test_mock_mcp_url_returns_mock_data(self):
        from app.ingestion.jobs.strava import scrape
        conn = _make_connection("strava", mcp_url="http://localhost:9000/mcp/strava")
        result = await scrape(conn)
        assert "km" in result
        assert len(result) > 10

    @pytest.mark.asyncio
    async def test_no_mcp_url_returns_mock_data(self):
        from app.ingestion.jobs.strava import scrape
        conn = _make_connection("strava", mcp_url=None)
        result = await scrape(conn)
        assert result  # non-empty

    @pytest.mark.asyncio
    async def test_real_mcp_url_calls_http(self):
        from app.ingestion.jobs.strava import scrape

        mock_result = {
            "activities": [
                {"name": "Morning Run", "distance": 5200, "elapsed_time": 1560},
            ]
        }

        with patch("app.ingestion.jobs._base.httpx.AsyncClient") as mock_client_cls:
            mock_response = MagicMock()
            mock_response.json.return_value = {"result": mock_result}
            mock_response.raise_for_status = MagicMock()
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=MagicMock(
                post=AsyncMock(return_value=mock_response)
            ))
            mock_context.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_context

            conn = _make_connection("strava", mcp_url="https://real.mcp.example.com/strava")
            result = await scrape(conn)
            assert "Morning Run" in result

    @pytest.mark.asyncio
    async def test_connection_error_returns_mock_data(self):
        from app.ingestion.jobs.strava import scrape
        import httpx as httpx_lib

        with patch("app.ingestion.jobs._base.httpx.AsyncClient") as mock_client_cls:
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=MagicMock(
                post=AsyncMock(side_effect=httpx_lib.RequestError("connection refused"))
            ))
            mock_context.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_context

            conn = _make_connection("strava", mcp_url="https://real.mcp.example.com/strava")
            result = await scrape(conn)
            assert result  # graceful fallback


class TestGmailJob:
    @pytest.mark.asyncio
    async def test_mock_url_returns_mock_data(self):
        from app.ingestion.jobs.gmail import scrape
        conn = _make_connection("gmail", mcp_url="http://localhost:9000/mcp/gmail")
        result = await scrape(conn)
        assert "email" in result.lower()


class TestAppleHealthJob:
    @pytest.mark.asyncio
    async def test_mock_url_returns_mock_data(self):
        from app.ingestion.jobs.apple_health import scrape
        conn = _make_connection("apple_health", mcp_url="http://localhost:9000/mcp/apple_health")
        result = await scrape(conn)
        assert "heart rate" in result.lower() or "steps" in result.lower()


# ---------------------------------------------------------------------------
# Ingestor
# ---------------------------------------------------------------------------

class TestIngestor:
    def _make_db(self):
        db = MagicMock()
        table = MagicMock()
        table.insert.return_value = table
        table.execute.return_value = MagicMock(data=[{"id": "mem-1"}])
        db.table.return_value = table
        return db

    @pytest.mark.asyncio
    async def test_skips_unknown_app(self):
        from app.ingestion.ingestor import Ingestor
        db = self._make_db()
        mock_summarizer = AsyncMock()
        mock_summarizer.summarize = AsyncMock(return_value=[])

        ingestor = Ingestor(db=db, summarizer=mock_summarizer)
        conn = _make_connection("unknown_app_xyz")
        await ingestor.ingest("proj-1", [conn])  # must not raise
        mock_summarizer.summarize.assert_not_called()

    @pytest.mark.asyncio
    async def test_calls_scraper_and_summarizer(self):
        from app.ingestion import ingestor as ingestor_mod
        from app.ingestion.ingestor import Ingestor
        db = self._make_db()
        mock_summarizer = MagicMock()
        mock_summarizer.summarize = AsyncMock(return_value=["- User runs 5km regularly"])
        mock_scraper = AsyncMock(return_value="5km run data")

        with patch.dict(ingestor_mod._SCRAPERS, {"strava": mock_scraper}):
            ingestor = Ingestor(db=db, summarizer=mock_summarizer)
            conn = _make_connection("strava")
            await ingestor.ingest("proj-1", [conn])

        mock_summarizer.summarize.assert_called_once_with("5km run data", "strava")

    @pytest.mark.asyncio
    async def test_writes_memory_entries_to_db(self):
        from app.ingestion.ingestor import Ingestor
        db = self._make_db()
        mock_summarizer = MagicMock()
        mock_summarizer.summarize = AsyncMock(
            return_value=["- Fact A", "- Fact B"]
        )

        with patch("app.ingestion.jobs.strava.scrape", new=AsyncMock(return_value="data")):
            ingestor = Ingestor(db=db, summarizer=mock_summarizer)
            conn = _make_connection("strava")
            await ingestor.ingest("proj-1", [conn])

        assert db.table.call_count == 2  # one insert per fact

    @pytest.mark.asyncio
    async def test_handles_empty_scrape_gracefully(self):
        from app.ingestion import ingestor as ingestor_mod
        from app.ingestion.ingestor import Ingestor
        db = self._make_db()
        mock_summarizer = MagicMock()
        mock_summarizer.summarize = AsyncMock(return_value=[])

        with patch.dict(ingestor_mod._SCRAPERS, {"strava": AsyncMock(return_value="")}):
            ingestor = Ingestor(db=db, summarizer=mock_summarizer)
            conn = _make_connection("strava")
            await ingestor.ingest("proj-1", [conn])  # must not raise

        mock_summarizer.summarize.assert_not_called()

    @pytest.mark.asyncio
    async def test_processes_multiple_connections(self):
        from app.ingestion import ingestor as ingestor_mod
        from app.ingestion.ingestor import Ingestor
        db = self._make_db()
        mock_summarizer = MagicMock()
        mock_summarizer.summarize = AsyncMock(return_value=["- A fact"])

        with patch.dict(ingestor_mod._SCRAPERS, {
            "strava": AsyncMock(return_value="strava data"),
            "gmail": AsyncMock(return_value="gmail data"),
        }):
            ingestor = Ingestor(db=db, summarizer=mock_summarizer)
            conns = [
                _make_connection("strava"),
                _make_connection("gmail", mcp_url="http://localhost:9000/mcp/gmail"),
            ]
            await ingestor.ingest("proj-1", conns)

        assert mock_summarizer.summarize.call_count == 2


# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------

class TestStateMachine:
    def _make_db(self, initial_status: str = "draft"):
        db = MagicMock()
        row = {"id": "proj-1", "status": initial_status}
        table = MagicMock()
        table.select.return_value = table
        table.update.return_value = table
        table.upsert.return_value = table
        table.eq.return_value = table
        table.execute.return_value = MagicMock(data=[row])
        db.table.return_value = table
        return db

    @pytest.mark.asyncio
    async def test_transitions_through_full_pipeline(self):
        from app.provisioning.state_machine import run_provisioning

        db = self._make_db()
        bundle = _make_bundle()
        connections = [_make_connection()]

        mock_provisioner = MagicMock()
        mock_handle = ProfileHandle(
            project_id="proj-123",
            gateway_url="http://localhost:8080",
            gateway_key="key",
            session_key=bundle.session_key,
            runtime_key=bundle.runtime_key,
            status=ProvisioningState.READY,
        )
        mock_provisioner.provision = AsyncMock(return_value=mock_handle)

        handle = await run_provisioning(db, "proj-123", bundle, connections, mock_provisioner)
        assert handle.status == ProvisioningState.READY

    @pytest.mark.asyncio
    async def test_transitions_to_failed_on_error(self):
        from app.provisioning.state_machine import run_provisioning

        db = self._make_db()
        bundle = _make_bundle()

        mock_provisioner = MagicMock()
        mock_provisioner.provision = AsyncMock(side_effect=RuntimeError("gateway down"))

        with pytest.raises(RuntimeError, match="gateway down"):
            await run_provisioning(db, "proj-123", bundle, [], mock_provisioner)

        # Last DB update should be FAILED
        calls = db.table.return_value.update.call_args_list
        last_payload = calls[-1][0][0]
        assert last_payload["status"] == "failed"

    @pytest.mark.asyncio
    async def test_transition_persists_status(self):
        from app.provisioning.state_machine import transition

        db = self._make_db()
        await transition(db, "proj-1", ProvisioningState.COMPILING)

        db.table.return_value.update.assert_called_once()
        payload = db.table.return_value.update.call_args[0][0]
        assert payload["status"] == "compiling"

    @pytest.mark.asyncio
    async def test_transition_persists_failed_stage(self):
        from app.provisioning.state_machine import transition

        db = self._make_db()
        await transition(db, "proj-1", ProvisioningState.FAILED, failed_stage="ingestor crash")

        payload = db.table.return_value.update.call_args[0][0]
        assert payload["status"] == "failed"
        assert payload["failed_stage"] == "ingestor crash"


# ---------------------------------------------------------------------------
# _build_mcp_yaml
# ---------------------------------------------------------------------------

class TestBuildMcpYaml:
    def test_empty_connections_returns_empty_string(self):
        from app.provisioning.hermes_writer import _build_mcp_yaml
        assert _build_mcp_yaml([]) == ""

    def test_pending_connection_excluded(self):
        from app.provisioning.hermes_writer import _build_mcp_yaml
        conn = _make_connection(status=ConnectionStatus.PENDING, mcp_url=None)
        assert _build_mcp_yaml([conn]) == ""

    def test_connected_app_included(self):
        from app.provisioning.hermes_writer import _build_mcp_yaml
        conn = _make_connection("strava")
        result = _build_mcp_yaml([conn])
        assert "mcp_servers:" in result
        assert "strava" in result
        assert "localhost:9000" in result

    def test_tools_listed(self):
        from app.provisioning.hermes_writer import _build_mcp_yaml
        conn = _make_connection("strava", tools=["get_activities", "get_athlete"])
        result = _build_mcp_yaml([conn])
        assert "get_activities" in result
        assert "get_athlete" in result

    def test_multiple_apps(self):
        from app.provisioning.hermes_writer import _build_mcp_yaml
        c1 = _make_connection("strava")
        c2 = _make_connection("gmail", mcp_url="http://localhost:9000/mcp/gmail")
        result = _build_mcp_yaml([c1, c2])
        assert result.count("- name:") == 2
