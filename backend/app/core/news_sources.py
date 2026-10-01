from app.core.config import settings


def _parse_urls(value: str) -> list[str]:
    urls = []
    for line in value.splitlines():
        urls.extend(part.strip() for part in line.split(","))
    return list(dict.fromkeys(url for url in urls if url))


def get_enabled_sources() -> dict:
    """Return only explicitly configured feed sources."""
    configured = {
        "news": settings.news_rss_urls,
        "kap": settings.kap_rss_urls,
    }
    return {
        name: {
            "enabled": bool(urls := _parse_urls(value)),
            "type": "rss",
            "urls": urls,
        }
        for name, value in configured.items()
    }
