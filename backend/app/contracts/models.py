"""Pydantic v2 contract models — the single source of truth for the API contract.

Generated from ARCHITECTURE.md §5 (DB schema) + ARCHITECTURE_UML.md §3 (class diagram).
Match: Supabase storage types + REST/SSE API contracts.
"""
from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ProvisioningState(str, Enum):
    DRAFT = "draft"
    COMPILING = "compiling"
    CONNECTING = "connecting"
    PROVISIONING = "provisioning"
    INGESTING = "ingesting"
    READY = "ready"
    FAILED = "failed"


class ConnectionStatus(str, Enum):
    PENDING = "pending"
    CONNECTED = "connected"
    ERROR = "error"


# ---------------------------------------------------------------------------
# ProjectSpec sub-models
# ---------------------------------------------------------------------------

class TaskItem(BaseModel):
    title: str
    description: str


class ToolRequirement(BaseModel):
    app: str
    reason: str
    needed_scopes: list[str] = Field(default_factory=list)
    tool_subset: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# ProjectSpec / ArtifactBundle
# ---------------------------------------------------------------------------

class ProjectSpec(BaseModel):
    name: str
    goal: str
    persona: str
    tasks: list[TaskItem] = Field(default_factory=list)
    tool_requirements: list[ToolRequirement] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    avatar_seed: str


class ArtifactBundle(BaseModel):
    soul_md: str
    user_md: str
    memory_md: str
    config_yaml: str
    runtime_key: str
    session_key: str
    tool_requirements: list[ToolRequirement] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Connection / ProfileHandle / Project
# ---------------------------------------------------------------------------

class AppCatalogItem(BaseModel):
    app: str
    display_name: str
    description: str
    icon: str
    default_scopes: list[str] = Field(default_factory=list)


class Connection(BaseModel):
    id: str
    user_id: str
    app: str
    status: ConnectionStatus
    mcp_url: str | None = None
    available_tools: list[str] = Field(default_factory=list)


class ProfileHandle(BaseModel):
    project_id: str
    gateway_url: str
    gateway_key: str
    session_key: str
    runtime_key: str
    status: ProvisioningState


class Project(BaseModel):
    id: str
    user_id: str
    name: str
    goal: str | None = None
    status: ProvisioningState
    failed_stage: str | None = None
    spec: ProjectSpec | None = None
    avatar_seed: str | None = None


# ---------------------------------------------------------------------------
# SSE Event Models — runtime (chat) stream
# ARCHITECTURE.md §8
# ---------------------------------------------------------------------------

class Msg(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class Delta(BaseModel):
    type: Literal["delta"] = "delta"
    text: str


class Action(BaseModel):
    type: Literal["action"] = "action"
    label: str
    detail: str | None = None


class Done(BaseModel):
    type: Literal["done"] = "done"


class Err(BaseModel):
    type: Literal["error"] = "error"
    message: str


# Union alias — the actual SSE wire type for the runtime chat stream.
RuntimeEvent = Delta | Action | Done | Err


# ---------------------------------------------------------------------------
# SSE Event Models — shaping (spec-creation) stream
# ARCHITECTURE_UML.md §3 — ShapingEvent
# ---------------------------------------------------------------------------

class QuestionPayload(BaseModel):
    field: str
    prompt: str
    options: list[str]


class ShapingDelta(BaseModel):
    type: Literal["delta"] = "delta"
    text: str


class ShapingQuestion(BaseModel):
    type: Literal["question"] = "question"
    question: QuestionPayload


class ShapingSpecUpdate(BaseModel):
    type: Literal["spec_update"] = "spec_update"
    spec_update: dict


class ShapingProposal(BaseModel):
    type: Literal["proposal"] = "proposal"
    spec: ProjectSpec
    suggested_apps: list[str] = Field(default_factory=list)


class ShapingDone(BaseModel):
    type: Literal["done"] = "done"


# Union alias — the actual SSE wire type for the shaping stream.
ShapingEvent = (
    ShapingDelta | ShapingQuestion | ShapingSpecUpdate | ShapingProposal | ShapingDone
)
