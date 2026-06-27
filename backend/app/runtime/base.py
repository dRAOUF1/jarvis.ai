"""AgentRuntime — the swap-able runtime interface.

All concrete implementations (MockRuntime, HermesRuntime) must subclass this
and implement the streaming `chat` method.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterable

from app.contracts import Msg, RuntimeEvent


class AgentRuntime(ABC):
    @abstractmethod
    async def chat(
        self,
        *,
        project_id: str,
        session_key: str,
        session_id: str,
        messages: list[Msg],
    ) -> AsyncIterable[RuntimeEvent]:
        """Stream RuntimeEvent objects for a chat interaction.

        Args:
            project_id: The project this conversation belongs to.
            session_key: Hermes session key (agent:{pid}:user:{uid}).
            session_id: Unique session identifier.
            messages: Full conversation history including the latest user msg.

        Yields:
            Delta, Action, Done, or Err events.
        """
        ...
