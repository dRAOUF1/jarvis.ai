"""POST /meta — free-text need → ProjectSpec (B1)."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["meta"])


class MetaRequest(BaseModel):
    need: str


@router.post("/meta")
async def meta_endpoint(body: MetaRequest):
    """One Claude call: free-text description → complete ProjectSpec.

    Used by the frontend to seed the shaping chat with an initial spec,
    or for quick one-shot project creation without the full interview.
    """
    from app.control.compiler import Compiler

    compiler = Compiler()
    spec = await compiler.generate_spec_from_need(body.need)
    return {"spec": spec.model_dump()}
