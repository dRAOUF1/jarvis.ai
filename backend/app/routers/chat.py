"""POST /projects/{project_id}/chat — SSE chat stream.
GET /projects/{project_id}/messages — message history.
"""

from __future__ import annotations

from collections.abc import AsyncIterable
from uuid import uuid4

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse, ServerSentEvent

from app.contracts import Msg
from app.db.queries import get_messages, get_project, insert_message
from app.deps import get_agent_runtime, get_db


router = APIRouter(tags=["chat"])


@router.get("/projects/{project_id}/messages")
def list_messages(project_id: str, db=Depends(get_db)):
    return {"messages": get_messages(db, project_id)}


@router.post("/projects/{project_id}/chat")
async def chat(
    project_id: str,
    body: dict,
    runtime=Depends(get_agent_runtime),
    db=Depends(get_db),
):
    """Start an SSE chat stream for a project.

    Body: {"message": "..."}.
    The user message is persisted, then the runtime streams the response.
    """
    user_msg = body.get("message", "")
    if not user_msg:
        return {"error": "message is required"}

    project = get_project(db, project_id)
    if not project:
        return {"error": "project not found"}

    # Persist user message
    insert_message(db, project_id, "user", user_msg)

    # Load full history
    history = get_messages(db, project_id)
    messages = [Msg(role=m["role"], content=m["content"]) for m in history]

    # Session key from project row
    session_key = project.get(
        "session_key", f"agent:{project_id}:user:{project.get('user_id', '')}"
    )

    async def event_generator() -> AsyncIterable[ServerSentEvent]:
        full_response: list[str] = []
        async for event in runtime.chat(
            project_id=project_id,
            session_key=session_key,
            session_id=str(uuid4()),
            messages=messages,
        ):
            yield ServerSentEvent(
                data=event.model_dump_json(),
                event=event.type,
            )
            # Accumulate delta text for persistence
            if event.type == "delta":
                full_response.append(event.text)

        # Persist the assistant response after the stream completes
        assistant_text = "".join(full_response)
        if assistant_text:
            insert_message(db, project_id, "assistant", assistant_text)

    return EventSourceResponse(event_generator())
