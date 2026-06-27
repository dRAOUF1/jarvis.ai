"""Runtime factory — return the correct AgentRuntime based on RUNTIME_MODE."""

from __future__ import annotations

from app.config import settings
from app.db.client import get_supabase
from app.runtime.base import AgentRuntime

_runtime: AgentRuntime | None = None


def get_runtime() -> AgentRuntime:
    """Return a singleton AgentRuntime instance.

    The concrete type is determined by settings.runtime_mode:
    - 'mock':   MockRuntime (Anthropic SDK direct)
    - 'hermes': HermesRuntime (gateway proxy)
    """
    global _runtime
    if _runtime is not None:
        return _runtime

    if settings.runtime_mode == "mock":
        from app.runtime.mock_runtime import MockRuntime

        _runtime = MockRuntime(db=get_supabase())
    else:
        from app.runtime.hermes_runtime import HermesRuntime

        _runtime = HermesRuntime(
            gateway_url=settings.hermes_a_url,
            gateway_key=settings.hermes_a_key,
        )

    return _runtime


def reset_runtime() -> None:
    """Clear the cached instance (useful for tests)."""
    global _runtime
    _runtime = None
