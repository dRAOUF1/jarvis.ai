"""Ingestor — orchestrates per-app scraping → summarization → memory DB writes."""

from __future__ import annotations

from supabase import Client

from app.contracts import Connection
from app.db.queries import insert_memory
from app.ingestion.summarizer import Summarizer

# Registry mapping app name → scrape function
_SCRAPERS: dict[str, object] = {}


def _get_scrapers() -> dict:
    """Lazy-import scrapers to avoid circular imports at module load."""
    if not _SCRAPERS:
        from app.ingestion.jobs import strava, gmail, apple_health
        _SCRAPERS["strava"] = strava.scrape
        _SCRAPERS["gmail"] = gmail.scrape
        _SCRAPERS["apple_health"] = apple_health.scrape
    return _SCRAPERS


class Ingestor:
    def __init__(self, db: Client, summarizer: Summarizer | None = None):
        self.db = db
        self.summarizer = summarizer or Summarizer()

    async def ingest(self, project_id: str, connections: list[Connection]) -> None:
        """Scrape each connected app, summarize, and write memory entries to DB."""
        scrapers = _get_scrapers()

        for connection in connections:
            scraper = scrapers.get(connection.app)
            if not scraper:
                continue

            raw_data: str = await scraper(connection)  # type: ignore[operator]
            if not raw_data.strip():
                continue

            facts = await self.summarizer.summarize(raw_data, connection.app)
            for fact in facts:
                insert_memory(self.db, project_id, "scraped", fact)
