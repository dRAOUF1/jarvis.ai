"""Typed query helpers — one namespace per table.

All helpers take a Supabase Client as the first argument so they can be
used anywhere without coupling to FastAPI Depends().
"""

from __future__ import annotations

from supabase import Client


# -- users -------------------------------------------------------------------

def get_user(db: Client, user_id: str) -> dict | None:
    res = db.table("users").select("*").eq("id", user_id).execute()
    return res.data[0] if res.data else None


def upsert_user(db: Client, user_id: str, name: str = "", email: str = "") -> dict:
    res = db.table("users").upsert(
        {"id": user_id, "name": name, "email": email}
    ).execute()
    return res.data[0] if res.data else {}


# -- projects ----------------------------------------------------------------

def get_projects(db: Client, user_id: str) -> list[dict]:
    res = (
        db.table("projects")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return res.data or []


def get_project(db: Client, project_id: str) -> dict | None:
    res = db.table("projects").select("*").eq("id", project_id).execute()
    return res.data[0] if res.data else None


def update_project_status(
    db: Client,
    project_id: str,
    status: str,
    failed_stage: str | None = None,
) -> dict:
    payload: dict = {"status": status}
    if failed_stage is not None:
        payload["failed_stage"] = failed_stage
    res = db.table("projects").update(payload).eq("id", project_id).execute()
    return res.data[0] if res.data else {}


def create_project(db: Client, data: dict) -> dict:
    res = db.table("projects").insert(data).execute()
    return res.data[0] if res.data else {}


# -- messages ----------------------------------------------------------------

def insert_message(db: Client, project_id: str, role: str, content: str) -> dict:
    res = (
        db.table("messages")
        .insert({"project_id": project_id, "role": role, "content": content})
        .execute()
    )
    return res.data[0] if res.data else {}


def get_messages(db: Client, project_id: str) -> list[dict]:
    res = (
        db.table("messages")
        .select("*")
        .eq("project_id", project_id)
        .order("created_at")
        .execute()
    )
    return res.data or []


# -- memory ------------------------------------------------------------------

def insert_memory(db: Client, project_id: str, kind: str, content: str) -> dict:
    res = (
        db.table("memory")
        .insert({"project_id": project_id, "kind": kind, "content": content})
        .execute()
    )
    return res.data[0] if res.data else {}


def get_memory(db: Client, project_id: str) -> list[dict]:
    res = (
        db.table("memory")
        .select("*")
        .eq("project_id", project_id)
        .order("created_at")
        .execute()
    )
    return res.data or []


# -- connections -------------------------------------------------------------

def get_connections(db: Client, user_id: str) -> list[dict]:
    res = (
        db.table("connections")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )
    return res.data or []


def get_connection(db: Client, connection_id: str) -> dict | None:
    res = db.table("connections").select("*").eq("id", connection_id).execute()
    return res.data[0] if res.data else None


def upsert_connection(db: Client, data: dict) -> dict:
    res = db.table("connections").upsert(data).execute()
    return res.data[0] if res.data else {}


# -- project_tools -----------------------------------------------------------

def get_project_tools(db: Client, project_id: str) -> list[dict]:
    res = (
        db.table("project_tools")
        .select("*, connections(*)")
        .eq("project_id", project_id)
        .execute()
    )
    return res.data or []
