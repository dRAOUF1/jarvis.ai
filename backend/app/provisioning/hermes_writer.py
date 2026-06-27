"""HermesWriter — stamp a profile directory from an ArtifactBundle + Connections.

Writes SOUL.md, USER.md, MEMORY.md, config.yaml (with MCP blocks) into
hermes/profiles/{project_id}/ and returns a ProfileHandle with a gateway slot.
"""

from __future__ import annotations

import re
from pathlib import Path

from app.contracts import ArtifactBundle, Connection, ConnectionStatus, ProfileHandle, ProvisioningState


# Path from this file: backend/app/provisioning/ → ../../../../hermes/profiles
_DEFAULT_PROFILES_DIR = Path(__file__).resolve().parents[3] / "hermes" / "profiles"


def _parse_project_id(session_key: str) -> str:
    """Extract project_id from 'agent:{project_id}:user:{user_id}'."""
    m = re.match(r"agent:([^:]+):user:", session_key)
    if not m:
        raise ValueError(f"Malformed session_key: {session_key!r}")
    return m.group(1)


def _build_mcp_yaml(connections: list[Connection]) -> str:
    """Build the mcp_servers YAML block from active connections."""
    active = [c for c in connections if c.status == ConnectionStatus.CONNECTED and c.mcp_url]
    if not active:
        return ""

    lines = ["mcp_servers:"]
    for conn in active:
        lines.append(f"  - name: {conn.app}")
        lines.append("    transport:")
        lines.append("      type: http")
        lines.append(f"      url: {conn.mcp_url}")
        if conn.available_tools:
            lines.append("    allowed_tools:")
            for tool in conn.available_tools:
                lines.append(f"      - {tool}")
    return "\n".join(lines) + "\n"


class HermesWriter:
    """Write a Hermes profile directory from an ArtifactBundle."""

    def __init__(self, profiles_dir: Path | None = None, gateway_registry=None):
        self.profiles_dir = profiles_dir or _DEFAULT_PROFILES_DIR
        self.gateway_registry = gateway_registry

    async def write(
        self, bundle: ArtifactBundle, connections: list[Connection]
    ) -> ProfileHandle:
        project_id = _parse_project_id(bundle.session_key)
        profile_dir = self.profiles_dir / project_id
        profile_dir.mkdir(parents=True, exist_ok=True)

        (profile_dir / "SOUL.md").write_text(bundle.soul_md, encoding="utf-8")
        (profile_dir / "USER.md").write_text(bundle.user_md, encoding="utf-8")
        (profile_dir / "MEMORY.md").write_text(bundle.memory_md, encoding="utf-8")

        config_content = bundle.config_yaml.rstrip("\n") + "\n"
        mcp_block = _build_mcp_yaml(connections)
        if mcp_block:
            config_content += "\n" + mcp_block
        (profile_dir / "config.yaml").write_text(config_content, encoding="utf-8")

        # Assign a gateway slot (falls back gracefully if none available)
        gateway_url = "http://localhost:8080"
        gateway_key = "mock-gateway-key"
        if self.gateway_registry:
            try:
                slot = self.gateway_registry.assign()
                gateway_url = slot.url
                gateway_key = slot.key
            except RuntimeError:
                pass  # no warm slots — stay with fallback for demo

        return ProfileHandle(
            project_id=project_id,
            gateway_url=gateway_url,
            gateway_key=gateway_key,
            session_key=bundle.session_key,
            runtime_key=bundle.runtime_key,
            status=ProvisioningState.READY,
        )
