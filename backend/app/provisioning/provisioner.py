"""ProfileProvisioner — the swap-able provisioning interface.

WarmPoolProvisioner assigns a warm Hermes gateway and returns a ProfileHandle.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.contracts import ArtifactBundle, Connection, ProfileHandle, ProvisioningState
from app.db.queries import get_project
from app.db.client import get_supabase


class ProfileProvisioner(ABC):
    @abstractmethod
    async def provision(
        self,
        bundle: ArtifactBundle,
        connections: list[Connection],
        project_id: str,
    ) -> ProfileHandle:
        """Write the profile, warm the gateway, ingest memory, return a handle."""
        ...

    @abstractmethod
    async def status(self, project_id: str) -> ProvisioningState:
        """Return the current provisioning state for a project."""
        ...


class WarmPoolProvisioner(ProfileProvisioner):
    """Assign a warm gateway from the pool, bind the profile, return ProfileHandle."""

    def __init__(
        self,
        *,
        hermes_writer,
        ingestor,
        gateway_registry,
    ):
        self.writer = hermes_writer
        self.ingestor = ingestor
        self.gateway = gateway_registry

    async def provision(
        self,
        bundle: ArtifactBundle,
        connections: list[Connection],
        project_id: str,
    ) -> ProfileHandle:
        # 1. Write profile from bundle templates
        profile_handle = await self.writer.write(bundle, connections)

        # 2. Ping the gateway to keep it warm
        await self.gateway.warm(profile_handle.gateway_url)

        # 3. Ingest initial memory
        await self.ingestor.ingest(project_id, connections)

        return ProfileHandle(
            project_id=project_id,
            gateway_url=profile_handle.gateway_url,
            gateway_key=profile_handle.gateway_key,
            session_key=bundle.session_key,
            runtime_key=bundle.runtime_key,
            status=ProvisioningState.READY,
        )

    async def status(self, project_id: str) -> ProvisioningState:
        project = get_project(get_supabase(), project_id)
        if not project:
            return ProvisioningState.DRAFT
        return ProvisioningState(project["status"])


def get_provisioner() -> ProfileProvisioner:
    """Factory — return the correct provisioner based on PROVISIONER_MODE."""
    from pathlib import Path

    from app.config import settings
    from app.provisioning.gateway import GatewayRegistry
    from app.provisioning.hermes_writer import HermesWriter
    from app.ingestion.ingestor import Ingestor
    from app.ingestion.summarizer import Summarizer
    from app.db.client import get_supabase

    gateway_registry = GatewayRegistry()

    if settings.provisioner_mode == "warmpool":
        profiles_dir = Path(__file__).resolve().parents[3] / "hermes" / "profiles"
        db = get_supabase()
        return WarmPoolProvisioner(
            hermes_writer=HermesWriter(profiles_dir, gateway_registry),
            ingestor=Ingestor(db, Summarizer()),
            gateway_registry=gateway_registry,
        )

    # Future: ModalProvisioner
    raise NotImplementedError(f"Unknown provisioner_mode: {settings.provisioner_mode}")
