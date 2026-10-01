from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

import feedparser
import requests


DEFAULT_TIMEOUT_SECONDS = 10
USER_AGENT = "BIST-Katilim-AI-Predictor/0.1"


def fetch_rss(
    url: str,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> list[dict]:
    """Fetch and normalize a single RSS/Atom feed with a bounded timeout."""
    if timeout <= 0:
        raise ValueError("RSS fetch timeout must be positive.")

    response = requests.get(
        url,
        timeout=timeout,
        headers={"User-Agent": USER_AGENT},
    )
    response.raise_for_status()

    feed = feedparser.parse(response.content)
    if feed.bozo and not feed.entries:
        raise RuntimeError("RSS feed could not be parsed.")

    results: list[dict] = []
    for entry in feed.entries:
        title = str(entry.get("title", "")).strip()
        link = str(entry.get("link", "")).strip()
        if not title or not link:
            continue

        results.append(
            {
                "title": title,
                "url": link,
                "source": _source_name(url),
                "published_at": _parse_published(entry),
                "content_hash": _content_hash(title, link),
            }
        )
    return results


def match_news_to_symbols(
    news_items: list[dict],
    symbols: list[str],
) -> list[dict]:
    """Match ticker strings on token boundaries in title and URL."""
    normalized_symbols = sorted(
        {str(symbol).strip().upper() for symbol in symbols if str(symbol).strip()},
        key=len,
        reverse=True,
    )
    matched: list[dict] = []
    for item in news_items:
        haystack = f"{item.get('title', '')} {item.get('url', '')}".upper()
        for symbol in normalized_symbols:
            if re.search(rf"(?<![A-Z0-9]){re.escape(symbol)}(?![A-Z0-9])", haystack):
                record = dict(item)
                record["symbol"] = symbol
                matched.append(record)
    return matched


def _parse_published(entry) -> datetime:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed:
        from calendar import timegm

        return datetime.fromtimestamp(timegm(parsed), tz=timezone.utc)
    return datetime.now(timezone.utc)


def _source_name(url: str) -> str:
    hostname = urlparse(url).hostname
    return hostname.lower() if hostname else "unknown"


def _content_hash(title: str, link: str) -> str:
    raw = f"{title}|{link}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
