"""Mock bundle + mock C2 components (hermes_writer, ingestor)."""

from __future__ import annotations

from app.contracts import (
    ArtifactBundle,
    Connection,
    ProfileHandle,
    ProvisioningState,
    ToolRequirement,
)


def get_mock_bundle() -> ArtifactBundle:
    """Hardcoded Sports Coach bundle for the demo."""
    return ArtifactBundle(
        soul_md=(
            "You are a personal sports coach AI agent. "
            "You help athletes track, analyze, and improve their performance. "
            "Be encouraging but honest — data doesn't lie."
        ),
        user_md="The user is an amateur runner who uses Strava for activity tracking.",
        memory_md="- Fact: User ran 5km yesterday in 25 minutes.",
        config_yaml="model: claude-sonnet-4-6\ntemperature: 0.7\nmax_tokens: 4096\n",
        runtime_key="slot-a",
        session_key="agent:demo-project:user:demo-user",
        tool_requirements=[
            ToolRequirement(
                app="strava",
                reason="Track running activities and performance data",
                needed_scopes=["read:activities"],
                tool_subset=["get_activities", "get_activity_detail"],
            ),
        ],
    )


class MockHermesWriter:
    """Mock C2 hermes_writer — returns a fake ProfileHandle without writing anything."""

    async def write(
        self, bundle: ArtifactBundle, connections: list[Connection]
    ) -> ProfileHandle:
        return ProfileHandle(
            project_id="demo-project",
            gateway_url="http://localhost:8080",
            gateway_key="mock-gateway-key",
            session_key=bundle.session_key,
            runtime_key=bundle.runtime_key,
            status=ProvisioningState.READY,
        )


class MockIngestor:
    """Mock C2 ingestor — no-op but logs."""

    async def ingest(self, project_id: str, connections: list[Connection]) -> None:
        print(f"[mock ingestor] ingested {len(connections)} connection(s) for {project_id}")
