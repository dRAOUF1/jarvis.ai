"""GET /projects — list projects for a user.
GET /projects/{project_id} — get a single project.
POST /projects — create a new project and kick off provisioning.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config import settings
from app.contracts import ProvisioningState
from app.db.queries import create_project, get_project, get_projects
from app.deps import get_agent_provisioner, get_db
from app.mocks.mock_bundle import get_mock_bundle
from app.mocks.mock_connections import get_mock_connections
from app.provisioning.state_machine import run_provisioning


router = APIRouter(prefix="/projects", tags=["projects"])


# --- Request models ---

class CreateProjectBody(BaseModel):
    """Minimal body for creating a project.

    TODO H6-H12: B1 will replace this with a compiler.compile() call
    that takes a full ProjectSpec and returns an ArtifactBundle.
    For now, we accept a spec dict and use a mock bundle.
    """
    name: str = "Untitled Project"
    goal: str | None = None
    avatar_seed: str | None = None
    connection_ids: list[str] = []


# --- GET endpoints (always available) ---

@router.get("")
def list_projects(db=Depends(get_db)):
    return {"projects": get_projects(db, settings.demo_user_id)}


@router.get("/{project_id}")
def get_project_by_id(project_id: str, db=Depends(get_db)):
    project = get_project(db, project_id)
    if not project:
        return {"error": "project not found"}
    return {"project": project}


# --- POST endpoint ---

@router.post("")
async def create_project_endpoint(
    body: CreateProjectBody,
    db=Depends(get_db),
    provisioner=Depends(get_agent_provisioner),
):
    """Create a new project, compile a bundle (mock for now), and provision it."""
    # 1. Create the project in DB with status=draft
    session_key = f"agent:PLACEHOLDER:user:{settings.demo_user_id}"
    project_data = {
        "user_id": settings.demo_user_id,
        "name": body.name,
        "goal": body.goal,
        "status": ProvisioningState.DRAFT.value,
        "spec": body.model_dump(),
        "session_key": session_key,
        "avatar_seed": body.avatar_seed,
    }
    project = create_project(db, project_data)

    # 2. Use mock bundle (TODO: replace with B1 compiler)
    bundle = get_mock_bundle()

    # 3. Use mock connections (TODO: replace with C1 connection resolver)
    connections = get_mock_connections()

    # 4. Run the full provisioning state machine
    handle = await run_provisioning(db, project["id"], bundle, connections, provisioner)

    # 5. Update session_key with actual project_id
    from app.db.queries import update_project_status
    real_session_key = f"agent:{project['id']}:user:{settings.demo_user_id}"
    update_project_status(db, project["id"], ProvisioningState.READY.value)

    return {"project": project, "handle": handle.model_dump()}
