NEWS_SOURCES = {
    "google_news": {
        "enabled": True,
        "type": "rss",
        "urls": [],
    },
    "kap": {
        "enabled": True,
        "type": "rss",
        "urls": [],
    },
}


def get_enabled_sources() -> dict:
    return {
        name: config
        for name, config in NEWS_SOURCES.items()
        if config.get("enabled", False)
    }
