from __future__ import annotations

from datetime import date
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.core.news_sources import get_enabled_sources
from app.services.kap_public import fetch_kap_public_search
from app.services.news import fetch_rss, match_news_to_symbols
from app.services.news_quality import validate_news_batch


MAX_FEEDS_PER_SOURCE = 10
MAX_KAP_SYMBOLS_PER_BATCH = 100
MARKET_TIMEZONE = ZoneInfo("Europe/Istanbul")


def collect_configured_news(
    symbols: list[str],
    published_on: date | None = None,
) -> dict:
    """Collect RSS items and one daily public KAP search per requested ticker."""
    normalized_symbols = sorted(
        {str(symbol).strip().upper() for symbol in symbols if str(symbol).strip()}
    )
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
                valid_items = _for_publication_day(
                    validation["valid_items"],
                    published_on,
                )
                raw_items.extend(
                    {**item, "source": source_name}
                    for item in valid_items
                )
                result["reachable"] = True
                result["items"] = len(valid_items)
                if validation["invalid"]:
                    result["invalid_items"] = validation["invalid"]
            except Exception as exc:
                # Do not expose provider response text or credential-bearing URLs.
                result["error"] = type(exc).__name__
            source_results.append(result)

    matched_items = (
        match_news_to_symbols(raw_items, normalized_symbols)
        if normalized_symbols
        else []
    )

    kap_items = []
    query_symbols = normalized_symbols[:MAX_KAP_SYMBOLS_PER_BATCH]
    for symbol in query_symbols:
        result = {
            "source": "kap_public",
            "symbol": symbol,
            "reachable": False,
            "items": 0,
            "error": None,
        }
        try:
            fetched_items = fetch_kap_public_search(symbol)
            validation = validate_news_batch(fetched_items)
            valid_items = _for_publication_day(
                validation["valid_items"],
                published_on,
            )
            kap_items.extend(valid_items)
            result["reachable"] = True
            result["items"] = len(valid_items)
            if validation["invalid"]:
                result["invalid_items"] = validation["invalid"]
        except Exception as exc:
            result["error"] = type(exc).__name__
        source_results.append(result)

    if len(normalized_symbols) > MAX_KAP_SYMBOLS_PER_BATCH:
        source_results.append(
            {
                "source": "kap_public",
                "reachable": False,
                "items": 0,
                "error": "BatchLimitExceeded",
            }
        )

    unique_items = {}
    for item in [*matched_items, *kap_items]:
        unique_items.setdefault(
            (item.get("symbol", ""), item["content_hash"]),
            item,
        )
    items = list(unique_items.values())

    return {
        "source_count": len(source_results),
        "reachable_sources": sum(result["reachable"] for result in source_results),
        "item_count": len(items),
        "items": items,
        "sources": source_results,
    }


def _for_publication_day(
    items: list[dict],
    published_on: date | None,
) -> list[dict]:
    if published_on is None:
        return items
    return [
        item
        for item in items
        if item["published_at"].astimezone(MARKET_TIMEZONE).date()
        == published_on
    ]
