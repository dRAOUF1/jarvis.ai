"""Gateway registry — manage warm Hermes gateway slots."""

from __future__ import annotations

from dataclasses import dataclass, field

import httpx

from app.config import settings


@dataclass
class GatewaySlot:
    url: str
    key: str
    project_id: str | None = None


class GatewayRegistry:
    """Registry of warm Hermes gateway slots.

    Parses pool URLs/keys from settings at construction time.
    """

    def __init__(self):
        self._slots: list[GatewaySlot] = []

        # Add dedicated A/B slots first
        if settings.hermes_a_url:
            self._slots.append(
                GatewaySlot(settings.hermes_a_url, settings.hermes_a_key)
            )
        if settings.hermes_b_url:
            self._slots.append(
                GatewaySlot(settings.hermes_b_url, settings.hermes_b_key)
            )

        # Add pool slots
        urls = settings.hermes_pool_urls.split(",") if settings.hermes_pool_urls else []
        keys = settings.hermes_pool_keys.split(",") if settings.hermes_pool_keys else []
        for url, key in zip(urls, keys):
            url, key = url.strip(), key.strip()
            if url and key:
                self._slots.append(GatewaySlot(url, key))

    def assign(self) -> GatewaySlot:
        """Assign a free slot. Round-robin for now."""
        for slot in self._slots:
            if slot.project_id is None:
                slot.project_id = "assigned"  # mark as taken
                return slot
        raise RuntimeError("No warm gateway slots available")

    async def warm(self, url: str) -> None:
        """Ping the gateway /health to keep it warm."""
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                await client.get(url.rstrip("/") + "/health")
            except httpx.RequestError:
                # Gateway may be down — don't fail provisioning
                pass
