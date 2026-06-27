"""GET /projects/{project_id}/status — provisioning state (Phase 5)."""

from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_db
from app.db.queries import get_project


router = APIRouter(tags=["provisioning"])


@router.get("/projects/{project_id}/status")
async def get_status(project_id: str, db=Depends(get_db)):
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="project not found")
    return {
        "status": project.get("status"),
        "failed_stage": project.get("failed_stage"),
    }
