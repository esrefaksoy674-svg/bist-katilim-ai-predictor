from __future__ import annotations

from datetime import date

from app.services.news_ingestion import collect_configured_news
from app.services.news_repository_factory import get_news_repository


def run_daily_news_collection(
    symbols: list[str],
    trading_date: date,
) -> dict:
    result = collect_configured_news(
        symbols=symbols,
        published_on=trading_date,
    )
    persisted = get_news_repository().save_many(result["items"])
    return {
        "trading_date": trading_date.isoformat(),
        "source_count": result["source_count"],
        "reachable_sources": result["reachable_sources"],
        "item_count": result["item_count"],
        "persisted_count": persisted,
        "sources": result["sources"],
    }
