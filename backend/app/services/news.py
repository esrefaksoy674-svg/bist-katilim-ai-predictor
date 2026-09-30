from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from urllib.parse import urlparse

import feedparser


def fetch_rss(url: str) -> list[dict]:
    """
    RSS/Atom kaynağından haberleri standart sözlük yapısına dönüştürür.
    Kaynak okunamazsa sistemi durdurmak yerine boş liste döndürür;
    ancak hata bilgisi ayrıca kaydedilebilir.
    """
    feed = feedparser.parse(url)

    results: list[dict] = []

    for entry in feed.entries:
        title = str(entry.get("title", "")).strip()
        link = str(entry.get("link", "")).strip()

        if not title or not link:
            continue

        published = _parse_published(entry)

        results.append(
            {
                "title": title,
                "url": link,
                "source": _source_name(url),
                "published_at": published,
                "content_hash": _content_hash(title, link),
            }
        )

    return results


def match_news_to_symbols(
    news_items: list[dict],
    symbols: list[str],
) -> list[dict]:
    """
    Haber başlığı/linki içerisinde Katılım sembolü geçen
    haberleri aday ilişki olarak işaretler.

    Bu yalnızca ilk eşleştirme katmanıdır.
    Daha sonra şirket adı, sektör ve haber içeriği
    üzerinden daha gelişmiş ilişkilendirme yapılacaktır.
    """
    normalized_symbols = {
        symbol.upper(): symbol.upper()
        for symbol in symbols
    }

    matched: list[dict] = []

    for item in news_items:
        haystack = (
            f"{item.get('title', '')} "
            f"{item.get('url', '')}"
        ).upper()

        found = [
            symbol
            for symbol in normalized_symbols
            if symbol in haystack
        ]

        if not found:
            continue

        for symbol in found:
            record = dict(item)
            record["symbol"] = symbol
            matched.append(record)

    return matched


def _parse_published(entry) -> datetime:
    parsed = entry.get("published_parsed")

    if parsed:
        from calendar import timegm

        return datetime.fromtimestamp(
            timegm(parsed),
            tz=timezone.utc,
        )

    parsed = entry.get("updated_parsed")

    if parsed:
        from calendar import timegm

        return datetime.fromtimestamp(
            timegm(parsed),
            tz=timezone.utc,
        )

    return datetime.now(timezone.utc)


def _source_name(url: str) -> str:
    hostname = urlparse(url).hostname

    if not hostname:
        return "unknown"

    return hostname.lower()


def _content_hash(title: str, link: str) -> str:
    raw = f"{title}|{link}".encode("utf-8")

    return hashlib.sha256(raw).hexdigest()
