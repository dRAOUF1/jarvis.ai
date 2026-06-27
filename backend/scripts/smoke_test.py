"""Headless hero-path test. Must pass before any merge to main after H16.

Tests: health → create project → check status → chat SSE.
Run with the backend server on localhost:8000.
"""

import asyncio
import json
import sys

import httpx

BASE = "http://localhost:8000"


async def test_hero_path() -> None:
    client = httpx.AsyncClient(timeout=30)

    try:
        # 1. Health check
        r = await client.get(f"{BASE}/health")
        assert r.status_code == 200, f"health: {r.status_code} {r.text}"
        data = r.json()
        assert data["status"] == "ok"
        print("[1/4] health OK")

        # 2. Create a project
        r = await client.post(
            f"{BASE}/projects",
            json={
                "name": "Test Coach",
                "goal": "Sports coaching",
                "avatar_seed": "coach",
                "connection_ids": [],
            },
        )
        assert r.status_code == 200, f"create: {r.status_code} {r.text}"
        body = r.json()
        project_id = body["project"]["id"]
        print(f"[2/4] create OK — project_id={project_id}")

        # 3. Check status (should be "ready" against mock)
        r = await client.get(f"{BASE}/projects/{project_id}/status")
        assert r.status_code == 200, f"status: {r.status_code} {r.text}"
        status = r.json()["status"]
        print(f"[3/4] status OK — {status}")

        # 4. Chat via SSE
        events: list[dict] = []
        async with client.stream(
            "POST",
            f"{BASE}/projects/{project_id}/chat",
            json={"message": "hello"},
        ) as resp:
            assert resp.status_code == 200, f"chat: {resp.status_code}"
            async for line in resp.aiter_lines():
                if line.startswith("event:"):
                    current_event = line[6:].strip()
                elif line.startswith("data:"):
                    data_str = line[5:].strip()
                    try:
                        events.append({"event": current_event, "data": json.loads(data_str)})
                    except json.JSONDecodeError:
                        events.append({"event": current_event, "data": data_str})

        assert len(events) > 0, "No SSE events received"
        event_types = [e["event"] for e in events]
        print(f"[4/4] chat OK — {len(events)} events: {event_types}")

        print("\nAll smoke tests passed!")

    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(test_hero_path())
