from __future__ import annotations

import hashlib
import re
import threading
import time
from datetime import datetime, timezone
from html import unescape
from urllib.parse import quote
from zoneinfo import ZoneInfo

import requests


KAP_SEARCH_URL = "https://www.kap.org.tr/tr/search/{symbol}/1"
REQUEST_TIMEOUT_SECONDS = 10
CACHE_TTL_SECONDS = 900
MIN_REQUEST_INTERVAL_SECONDS = 1.0
MAX_RESULTS = 10
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{2,10}$")
DISCLOSURE_LINK = re.compile(r'href=["\']([^"\']*/tr/Bildirim/([0-9]+)[^"\']*)["\']', re.IGNORECASE)
PUBLISHED_DATE = re.compile(r"\b(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}(?::\d{2})?)\b")

_cache: dict[str, tuple[float, list[dict]]] = {}
_cache_lock = threading.Lock()
_last_request_at = 0.0


def fetch_kap_public_search(symbol: str) -> list[dict]:
    """Fetch one bounded public KAP search page for a ticker, with caching.

    Use once per ticker in the end-of-day scan. This public-page reader is not
    the contracted KAP Data Dissemination REST API and must not be used for
    intraday or high-volume polling.
    """
    global _last_request_at

    normalized = str(symbol).strip().upper()
    if not SYMBOL_PATTERN.fullmatch(normalized):
        raise ValueError("A valid ticker symbol is required.")

    with _cache_lock:
        now = time.monotonic()
        cached = _cache.get(normalized)
        if cached and cached[0] > now:
            return [dict(item) for item in cached[1]]

        wait_seconds = MIN_REQUEST_INTERVAL_SECONDS - (now - _last_request_at)
        if wait_seconds > 0:
            time.sleep(wait_seconds)

        _last_request_at = time.monotonic()
        url = KAP_SEARCH_URL.format(symbol=quote(normalized, safe=""))
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT_SECONDS,
            headers={
                "User-Agent": "BIST-Katilim-AI-Predictor/0.1 (+public disclosure lookup)",
                "Accept": "text/html",
            },
        )
        response.raise_for_status()
        items = _parse_search_page(response.text, normalized)

        expires_at = time.monotonic() + CACHE_TTL_SECONDS
        if len(_cache) >= 128:
            _cache.clear()
        _cache[normalized] = (expires_at, items)
        return [dict(item) for item in items]


def _parse_search_page(html: str, symbol: str) -> list[dict]:
    links = []
    seen_ids = set()
    for match in DISCLOSURE_LINK.finditer(html):
        disclosure_id = match.group(2)
        if disclosure_id in seen_ids:
            continue
        seen_ids.add(disclosure_id)
        links.append("https://www.kap.org.tr/tr/Bildirim/" + disclosure_id)
        if len(links) >= MAX_RESULTS:
            break

    if not links:
        return []

    visible_text = re.sub(
        r"<(script|style)\b[^>]*>.*?</\1>",
        " ",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    visible_text = unescape(re.sub(r"<[^>]+>", " ", visible_text))
    published_dates = PUBLISHED_DATE.findall(visible_text)

    items = []
    for index, url in enumerate(links):
        if index >= len(published_dates):
            continue
        published_at = _parse_kap_date(published_dates[index])
        disclosure_id = url.rsplit("/", 1)[-1]
        title = _disclosure_title(html, disclosure_id)
        if not title:
            continue
        items.append(
            {
                "title": title,
                "url": url,
                "source": "kap.org.tr",
                "published_at": published_at,
                "content_hash": hashlib.sha256(
                    f"{title}|{url}".encode("utf-8")
                ).hexdigest(),
                "symbol": symbol,
            }
        )
    return items


def _disclosure_title(html: str, disclosure_id: str) -> str:
    pattern = re.compile(
        r'<a\b[^>]*href=["\'][^"\']*/tr/Bildirim/'
        + re.escape(disclosure_id)
        + r'[^"\']*["\'][^>]*>(.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(html)
    if not match:
        return ""
    title = unescape(re.sub(r"<[^>]+>", " ", match.group(1)))
    return " ".join(title.split())


def _parse_kap_date(value: str) -> datetime:
    for date_format in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
        try:
            local_time = datetime.strptime(value, date_format).replace(
                tzinfo=ZoneInfo("Europe/Istanbul")
            )
            return local_time.astimezone(timezone.utc)
        except ValueError:
            continue
    raise ValueError("KAP search page returned an invalid timestamp.")
