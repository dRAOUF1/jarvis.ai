"""MockRuntime — Anthropic SDK direct, no Hermes gateway needed.

Used when RUNTIME_MODE=mock. Falls back to simple mock data when no API key
is available (demo mode).
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterable

from supabase import Client

from app.config import settings
from app.contracts import Action, Delta, Done, Err, Msg, RuntimeEvent
from app.db.queries import get_memory
from app.runtime.base import AgentRuntime


class MockRuntime(AgentRuntime):
    """Chat directly against Anthropic (or a canned response for demo)."""

    def __init__(self, db: Client):
        self.db = db

    async def chat(
        self,
        *,
        project_id: str,
        session_key: str,
        session_id: str,
        messages: list[Msg],
    ) -> AsyncIterable[RuntimeEvent]:
        try:
            # Build system prompt from project memory
            memory = get_memory(self.db, project_id)
            system_prompt = self._build_system_prompt(memory) if memory else None

            api_key = settings.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
            if api_key:
                # Real Anthropic streaming
                async for event in self._chat_anthropic(messages, system_prompt, api_key):
                    yield event
            else:
                # Canned demo response
                async for event in self._chat_demo(messages):
                    yield event

        except Exception as e:
            yield Err(message=str(e))

    def _build_system_prompt(self, memory: list[dict]) -> str:
        lines = ["You are a helpful project agent embedded in jarvis.ai."]
        for entry in memory:
            lines.append(f"- [{entry['kind']}] {entry['content']}")
        return "\n".join(lines)

    async def _chat_anthropic(
        self, messages: list[Msg], system_prompt: str | None, api_key: str
    ) -> AsyncIterable[RuntimeEvent]:
        """Stream from Anthropic SDK."""
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=api_key)

        msg_list = [{"role": m.role, "content": m.content} for m in messages]
        kwargs: dict = {
            "model": "claude-sonnet-4-6",
            "max_tokens": 4096,
            "messages": msg_list,
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        async with client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield Delta(text=text)

        yield Action(label="done", detail="Response complete")
        yield Done()

    async def _chat_demo(
        self, messages: list[Msg]
    ) -> AsyncIterable[RuntimeEvent]:
        """Canned demo response (no API key)."""
        from app.mocks.mock_runtime_data import get_demo_response

        last_user = next(
            (m.content for m in reversed(messages) if m.role == "user"), ""
        )
        response = get_demo_response(last_user)

        # Simulate streaming with chunks
        words = response.split()
        for i, word in enumerate(words):
            yield Delta(text=word + (" " if i < len(words) - 1 else ""))

        yield Action(label="done", detail="Response complete (demo mode)")
        yield Done()
