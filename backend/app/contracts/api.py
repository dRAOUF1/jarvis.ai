"""Request/response wrapper models for each endpoint.

These are thin envelope models — not frozen contracts themselves.
The frozen types are the Pydantic models in models.py.
"""
from __future__ import annotations

from pydantic import BaseModel

from .models import Connection, Project, ProjectSpec


class ProjectsResponse(BaseModel):
    projects: list[Project]


class ProjectResponse(BaseModel):
    project: Project


class ConnectionsResponse(BaseModel):
    connections: list[Connection]


class MetaResponse(BaseModel):
    spec: ProjectSpec


class StatusResponse(BaseModel):
    status: str
    failed_stage: str | None = None
