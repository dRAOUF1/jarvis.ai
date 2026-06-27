"""HermesRuntime — POST to Hermes gateway for streaming completions.

Used when RUNTIME_MODE=hermes. Sends the session key and messages to the
Hermes gateway which proxies to the provisioned Claude instance.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterable

import httpx

from app.contracts import Action, Delta, Done, Err, Msg, RuntimeEvent
from app.runtime.base import AgentRuntime


class HermesRuntime(AgentRuntime):
    """Chat via a Hermes gateway.

    Args:
        gateway_url: Base URL of the Hermes gateway (e.g. http://localhost:8080).
        gateway_key: API key for authenticating with the gateway.
    """

    def __init__(self, gateway_url: str, gateway_key: str):
        self.gateway_url = gateway_url.rstrip("/")
        self.gateway_key = gateway_key

    async def chat(
        self,
        *,
        project_id: str,
        session_key: str,
        session_id: str,
        messages: list[Msg],
    ) -> AsyncIterable[RuntimeEvent]:
        headers = {
            "Authorization": f"Bearer {self.gateway_key}",
            "X-Hermes-Session-Key": session_key,
            "X-Hermes-Session-Id": session_id,
            "Content-Type": "application/json",
        }
        payload = {
            "model": "claude-sonnet-4-6",
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
        }

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                async with client.stream(
                    "POST",
                    f"{self.gateway_url}/v1/chat/completions",
                    json=payload,
                    headers=headers,
                ) as response:
                    if response.status_code != 200:
                        body = await response.aread()
                        yield Err(
                            message=f"Hermes gateway error {response.status_code}: {body.decode()}"
                        )
                        return

                    async for line in response.aiter_lines():
                        event = self._parse_sse_line(line)
                        if event is not None:
                            yield event

        except httpx.RequestError as e:
            yield Err(message=f"Connection to Hermes failed: {e}")
        except Exception as e:
            yield Err(message=str(e))

    def _parse_sse_line(self, line: str) -> RuntimeEvent | None:
        """Parse one SSE line into a RuntimeEvent.

        Expected format:
            data: {"type": "delta", "text": "..."}
            data: {"type": "done"}
            data: {"type": "error", "message": "..."}
            data: [DONE]          (OpenAI-style terminator)
        """
        if not line or not line.startswith("data: "):
            return None

        data = line[6:]  # strip "data: "

        if data == "[DONE]":
            return Done()

        try:
            obj = json.loads(data)
        except json.JSONDecodeError:
            return None

        event_type = obj.get("type", "")

        if event_type == "delta":
            return Delta(text=obj.get("text", ""))
        elif event_type == "action":
            return Action(label=obj.get("label", ""), detail=obj.get("detail"))
        elif event_type == "done":
            return Done()
        elif event_type == "error":
            return Err(message=obj.get("message", "unknown error"))
        else:
            return None
