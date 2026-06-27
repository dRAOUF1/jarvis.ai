"""Summarizer — one Claude call turns raw app data into structured memory entries."""

from __future__ import annotations

import anthropic

from app.config import settings

_SYSTEM = (
    "You are a memory extraction assistant. "
    "Given raw data from a connected app, extract concise factual memory entries "
    "about the user. Each entry must be a single sentence starting with '- '. "
    "Focus on facts, preferences, patterns, and achievements. "
    "Return only the bullet list, nothing else. Maximum 10 entries."
)


class Summarizer:
    def __init__(self, client: anthropic.Anthropic | None = None):
        self._client = client or anthropic.Anthropic(api_key=settings.anthropic_api_key)

    async def summarize(self, raw_data: str, app: str) -> list[str]:
        """Return memory bullet points from raw scraped data."""
        if not raw_data.strip():
            return []

        prompt = f"App: {app}\n\nRaw data:\n{raw_data}"

        # Synchronous call wrapped — Anthropic SDK has no native async yet
        response = self._client.messages.create(
            model="claude-haiku-4-5-20251001",  # cheapest model, quick summarization
            max_tokens=512,
            system=_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text
        return [line.strip() for line in text.splitlines() if line.strip().startswith("- ")]
