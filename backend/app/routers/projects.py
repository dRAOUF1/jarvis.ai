"""GET /projects — list projects for a user.
GET /projects/{project_id} — get a single project.
POST /projects — create a new project and kick off provisioning.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.contracts import Connection, ConnectionStatus, ProjectSpec, ProvisioningState
from app.db.queries import create_project, get_connection, get_project, get_projects
from app.deps import get_agent_provisioner, get_db
from app.mocks.mock_connections import get_mock_connections
from app.provisioning.state_machine import run_provisioning


router = APIRouter(prefix="/projects", tags=["projects"])


# --- Request models ---

class CreateProjectBody(BaseModel):
    """Body for POST /projects (ARCHITECTURE.md §6)."""
    spec: ProjectSpec
    connection_ids: list[str] = []


# --- GET endpoints ---

@router.get("")
def list_projects(db=Depends(get_db)):
    return {"projects": get_projects(db, settings.demo_user_id)}


@router.get("/{project_id}")
def get_project_by_id(project_id: str, db=Depends(get_db)):
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="project not found")
    return {"project": project}


# --- POST endpoint ---

@router.post("")
async def create_project_endpoint(
    body: CreateProjectBody,
    db=Depends(get_db),
    provisioner=Depends(get_agent_provisioner),
):
    """Compile spec → bundle, resolve connections, run provisioning state machine."""
    spec = body.spec

    # 1. Create the project row in DB (session_key updated once we have the UUID)
    project_data = {
        "user_id": settings.demo_user_id,
        "name": spec.name,
        "goal": spec.goal,
        "status": ProvisioningState.DRAFT.value,
        "spec": spec.model_dump(),
        "session_key": f"agent:PLACEHOLDER:user:{settings.demo_user_id}",
        "avatar_seed": spec.avatar_seed,
    }
    project = create_project(db, project_data)
    project_id = project["id"]

    # Fix session_key now that we have the real UUID
    from app.db.queries import update_project_status  # noqa: F401 (reuse db path)
    db.table("projects").update(
        {"session_key": f"agent:{project_id}:user:{settings.demo_user_id}"}
    ).eq("id", project_id).execute()
    project["session_key"] = f"agent:{project_id}:user:{settings.demo_user_id}"

    # 2. Compile spec → ArtifactBundle (B1)
    from app.control.compiler import Compiler
    bundle = await Compiler().compile(spec, project_id=project_id, user_id=settings.demo_user_id)

    # 3. Resolve connections — use real ones from DB if provided, fall back to mock (C1 fills this)
    if body.connection_ids:
        raw = [get_connection(db, cid) for cid in body.connection_ids]
        connections = [
            Connection(
                id=c["id"],
                user_id=c["user_id"],
                app=c["app"],
                status=ConnectionStatus(c["status"]),
                mcp_url=c.get("mcp_url"),
                available_tools=c.get("scopes") or [],
            )
            for c in raw if c
        ]
    else:
        connections = get_mock_connections()

    # 4. Run provisioning state machine
    handle = await run_provisioning(db, project_id, bundle, connections, provisioner)

    return {"project": {**project, "id": project_id}, "handle": handle.model_dump()}
