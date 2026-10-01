from __future__ import annotations

from app.core.config import settings
from app.core.news_sources import get_enabled_sources
from app.services.news import fetch_rss, match_news_to_symbols
from app.services.news_quality import validate_news_batch


MAX_FEEDS_PER_SOURCE = 10


def collect_configured_news(symbols: list[str]) -> dict:
    """Collect, validate, deduplicate, and optionally match configured RSS items."""
    sources = get_enabled_sources()
    raw_items: list[dict] = []
    source_results = []

    for source_name, config in sources.items():
        if not config.get("enabled"):
            continue
        for url in config.get("urls", [])[:MAX_FEEDS_PER_SOURCE]:
            result = {
                "source": source_name,
                "reachable": False,
                "items": 0,
                "error": None,
            }
            try:
                items = fetch_rss(url, timeout=settings.news_fetch_timeout_seconds)
                validation = validate_news_batch(items)
                valid_items = validation["valid_items"]
                raw_items.extend({**item, "source": source_name} for item in valid_items)
                result["reachable"] = True
                result["items"] = len(valid_items)
                if validation["invalid"]:
                    result["invalid_items"] = validation["invalid"]
            except Exception as exc:
                # Avoid returning provider response bodies or credential-bearing URLs.
                result["error"] = type(exc).__name__
            source_results.append(result)

    unique_items = {}
    for item in raw_items:
        unique_items.setdefault(item["content_hash"], item)

    items = list(unique_items.values())
    if symbols:
        items = match_news_to_symbols(items, symbols)

    return {
        "source_count": len(source_results),
        "reachable_sources": sum(result["reachable"] for result in source_results),
        "item_count": len(items),
        "items": items,
        "sources": source_results,
    }
