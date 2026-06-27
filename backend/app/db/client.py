"""Supabase client singleton."""

from supabase import Client, create_client

from app.config import settings

_supabase: Client | None = None


def get_supabase() -> Client:
    """Return the (cached) Supabase client."""
    global _supabase
    if _supabase is None:
        _supabase = create_client(settings.supabase_url, settings.supabase_service_role_key)
    return _supabase


def reset_supabase() -> None:
    """Clear the cached client (useful for tests)."""
    global _supabase
    _supabase = None
