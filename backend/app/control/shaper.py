"""Shaper — slot-filling interview agent.

Drives a multi-turn conversation with Claude using tool_calling to progressively
fill a ProjectSpec. Streams ShapingEvents back to the caller.

Each call is stateless: the client sends the full conversation history.
"""
from __future__ import annotations

import json
from collections.abc import AsyncIterator

from app.contracts import (
    ProjectSpec,
    QuestionPayload,
    ShapingDelta,
    ShapingDone,
    ShapingEvent,
    ShapingProposal,
    ShapingQuestion,
    ShapingSpecUpdate,
    TaskItem,
    ToolRequirement,
)
from app.control.catalog import CATALOG, get_catalog
from app.control.llm import MODEL, get_client

# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

_SHAPER_TOOLS = [
    {
        "name": "ask_question",
        "description": (
            "Ask the user a focused question to gather missing information for the spec. "
            "Use this when you need 1-2 more pieces of info before the spec is complete."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "field": {
                    "type": "string",
                    "description": "Which spec field this question is about (e.g. 'goal', 'tasks', 'apps')",
                },
                "prompt": {
                    "type": "string",
                    "description": "The question to ask the user (friendly, conversational)",
                },
                "options": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional 2-4 suggested answers to help the user",
                },
            },
            "required": ["field", "prompt"],
        },
    },
    {
        "name": "propose_spec",
        "description": (
            "Present a complete project specification to the user for confirmation. "
            "Call this only when you have enough information for a full, useful spec. "
            "Required: name, goal, persona, at least one task, success_criteria, avatar_seed."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "spec": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "goal": {"type": "string"},
                        "persona": {"type": "string"},
                        "tasks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "description": {"type": "string"},
                                },
                                "required": ["title", "description"],
                            },
                            "minItems": 1,
                        },
                        "tool_requirements": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "app": {"type": "string"},
                                    "reason": {"type": "string"},
                                    "needed_scopes": {"type": "array", "items": {"type": "string"}},
                                    "tool_subset": {"type": "array", "items": {"type": "string"}},
                                },
                                "required": ["app", "reason"],
                            },
                        },
                        "success_criteria": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 1,
                        },
                        "avatar_seed": {"type": "string"},
                    },
                    "required": [
                        "name", "goal", "persona", "tasks", "success_criteria", "avatar_seed",
                    ],
                },
                "suggested_apps": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "App IDs to recommend connecting (e.g. ['strava', 'gmail'])",
                },
            },
            "required": ["spec", "suggested_apps"],
        },
    },
]

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_CATALOG_SUMMARY = ", ".join(
    f"{app.id} ({app.description})" for app in CATALOG
)

_SYSTEM = f"""You are a friendly project setup assistant for jarvis.ai. Your job is to interview \
the user and gather all information needed to create their AI agent.

Required spec fields:
- name: short memorable agent name (2-4 words)
- goal: one clear purpose sentence
- persona: personality and communication style (e.g. "Encouraging and data-driven, speaks plainly")
- tasks: 2-4 specific capabilities of the agent
- success_criteria: 1-3 measurable outcomes
- avatar_seed: 1-2 emoji representing the agent

Optional but valuable:
- tool_requirements: apps to connect (recommend based on the goal)

Available apps: {_CATALOG_SUMMARY}

Interview rules:
1. Keep it conversational — ask at most 1-2 questions per turn.
2. Suggest relevant apps once you understand the goal.
3. Infer reasonable defaults (don't ask for avatar_seed — pick it yourself based on the goal).
4. When you have enough info for a complete, useful spec, call propose_spec immediately.
5. If the user confirms a proposal or says "looks good", finalize with propose_spec.

Start by warmly welcoming the user and asking what kind of agent they want to create.
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def shape_stream(
    messages: list[dict],
) -> AsyncIterator[ShapingEvent]:
    """Drive one turn of the shaping interview.

    `messages` is the full conversation history (role/content dicts) including
    the user's latest message. Yields ShapingEvents for the SSE stream.
    """
    client = get_client()

    # Anthropic requires alternating user/assistant turns
    msg_list = [{"role": m["role"], "content": m["content"]} for m in messages]

    # Ensure the conversation starts with a user message
    if not msg_list or msg_list[0]["role"] != "user":
        msg_list = [{"role": "user", "content": "Hello, I'd like to create an agent."}] + msg_list

    try:
        async with client.messages.stream(
            model=MODEL,
            max_tokens=1024,
            system=_SYSTEM,
            messages=msg_list,
            tools=_SHAPER_TOOLS,
            tool_choice={"type": "auto"},
        ) as stream:
            # Stream text deltas in real time
            async for text in stream.text_stream:
                yield ShapingDelta(text=text)

            # Process tool calls from the completed message
            final_msg = await stream.get_final_message()

            for block in final_msg.content:
                if block.type != "tool_use":
                    continue

                if block.name == "ask_question":
                    yield ShapingQuestion(
                        question=QuestionPayload(
                            field=block.input.get("field", ""),
                            prompt=block.input["prompt"],
                            options=block.input.get("options", []),
                        )
                    )

                elif block.name == "propose_spec":
                    try:
                        raw_spec = block.input["spec"]
                        raw_spec.setdefault("tool_requirements", [])
                        spec = ProjectSpec(**raw_spec)
                        yield ShapingProposal(
                            spec=spec,
                            suggested_apps=block.input.get("suggested_apps", []),
                        )
                    except Exception as exc:
                        yield ShapingDelta(text=f"\n\n[Could not build spec: {exc}]")

    except Exception as exc:
        yield ShapingDelta(text=f"\n\n[Error: {exc}]")

    yield ShapingDone()
