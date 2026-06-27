"""POST /projects/shape — SSE shaping stream (B1)."""
from __future__ import annotations

import json

from fastapi import APIRouter
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.contracts import ShapingDone, ShapingEvent

router = APIRouter(tags=["shaping"])


class ShapeRequest(BaseModel):
    message: str
    history: list[dict] = []


@router.post("/projects/shape")
async def shape_stream(body: ShapeRequest):
    """Stream a shaping interview turn as SSE.

    The client sends the new `message` + full prior `history` (role/content dicts).
    Returns a stream of ShapingEvents: delta | question | spec_update | proposal | done.
    """
    from app.control.shaper import shape_stream as _shape

    messages = list(body.history) + [{"role": "user", "content": body.message}]

    async def generate():
        async for event in _shape(messages):
            yield {"data": event.model_dump_json()}

    return EventSourceResponse(generate())
