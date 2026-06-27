"""FastAPI dependency providers."""

from fastapi import Depends
from supabase import Client

from app.db.client import get_supabase


def get_db() -> Client:
    """Yield a Supabase client for the request lifetime."""
    yield get_supabase()


def get_agent_runtime():
    """Return the AgentRuntime instance (mock or Hermes)."""
    from app.runtime.factory import get_runtime
    return get_runtime()


def get_agent_provisioner():
    """Return the ProfileProvisioner instance."""
    from app.provisioning.provisioner import get_provisioner
    return get_provisioner()
