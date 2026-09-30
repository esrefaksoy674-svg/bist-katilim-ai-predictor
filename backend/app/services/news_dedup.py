from __future__ import annotations

import hashlib


def create_news_hash(
    title: str,
    url: str,
) -> str:
    """
    Haber için deterministik benzersiz kimlik oluşturur.
    """

    normalized_title = " ".join(
        title.lower().split()
    )

    normalized_url = url.strip().lower()

    raw = (
        f"{normalized_title}|{normalized_url}"
    ).encode("utf-8")

    return hashlib.sha256(raw).hexdigest()


def deduplicate_news(
    items: list[dict],
) -> list[dict]:
    """
    Aynı haberin birden fazla kez kaydedilmesini önler.
    """

    unique: list[dict] = []
    seen: set[str] = set()

    for item in items:
        title = str(
            item.get("title", "")
        ).strip()

        url = str(
            item.get("url", "")
        ).strip()

        if not title or not url:
            continue

        content_hash = create_news_hash(
            title=title,
            url=url,
        )

        if content_hash in seen:
            continue

        seen.add(content_hash)

        record = dict(item)
        record["content_hash"] = content_hash

        unique.append(record)

    return unique
