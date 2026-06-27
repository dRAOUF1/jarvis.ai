"""Anthropic client wrapper — shared by shaper, compiler, and ingestion summarizer."""
from __future__ import annotations

import anthropic

from app.config import settings

MODEL = "claude-sonnet-4-6"

_client: anthropic.AsyncAnthropic | None = None


def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client
