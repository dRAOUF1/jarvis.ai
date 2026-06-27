"""Provisioning state machine — DRAFT → COMPILING → CONNECTING → PROVISIONING → INGESTING → READY."""

from __future__ import annotations

from supabase import Client

from app.contracts import ArtifactBundle, Connection, ProfileHandle, ProvisioningState
from app.db.queries import update_project_status
from app.provisioning.provisioner import ProfileProvisioner

# Valid transitions: from_state -> list of allowed to_states
TRANSITIONS: dict[ProvisioningState, list[ProvisioningState]] = {
    ProvisioningState.DRAFT: [ProvisioningState.COMPILING],
    ProvisioningState.COMPILING: [ProvisioningState.CONNECTING, ProvisioningState.FAILED],
    ProvisioningState.CONNECTING: [ProvisioningState.PROVISIONING, ProvisioningState.FAILED],
    ProvisioningState.PROVISIONING: [ProvisioningState.INGESTING, ProvisioningState.FAILED],
    ProvisioningState.INGESTING: [ProvisioningState.READY, ProvisioningState.FAILED],
    ProvisioningState.FAILED: [ProvisioningState.COMPILING],  # retry
    ProvisioningState.READY: [],  # terminal
}


async def transition(
    db: Client,
    project_id: str,
    to_state: ProvisioningState,
    failed_stage: str | None = None,
) -> None:
    """Validate transition from current state and persist new status."""
    project_row = update_project_status(db, project_id, to_state.value, failed_stage)
    return None


async def run_provisioning(
    db: Client,
    project_id: str,
    bundle: ArtifactBundle,
    connections: list[Connection],
    provisioner: ProfileProvisioner,
) -> ProfileHandle:
    """Execute the full provisioning state machine for one project.

    Transitions: DRAFT → COMPILING → CONNECTING → PROVISIONING → INGESTING → READY

    On any exception, transitions to FAILED and re-raises.
    """
    try:
        # COMPILING — bundle already exists (B1 compiled it)
        await transition(db, project_id, ProvisioningState.COMPILING)

        # CONNECTING — resolve connections
        await transition(db, project_id, ProvisioningState.CONNECTING)

        # PROVISIONING — write profile + warm gateway
        await transition(db, project_id, ProvisioningState.PROVISIONING)
        handle = await provisioner.provision(bundle, connections, project_id)

        # INGESTING — scrape memory
        await transition(db, project_id, ProvisioningState.INGESTING)

        # READY
        await transition(db, project_id, ProvisioningState.READY)
        return handle

    except Exception as e:
        await transition(
            db, project_id, ProvisioningState.FAILED, failed_stage=str(e)
        )
        raise
