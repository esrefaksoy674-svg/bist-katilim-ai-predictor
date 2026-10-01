from __future__ import annotations

from typing import Any


class NewsRepository:
    def save_many(self, items: list[dict]) -> int:
        raise NotImplementedError


class SupabaseNewsRepository(NewsRepository):
    table_name = "news_items"
    batch_size = 250

    def __init__(self, client: Any):
        self.client = client

    @staticmethod
    def _to_row(item: dict) -> dict:
        return {
            "symbol": str(item["symbol"]).upper(),
            "title": item["title"],
            "url": item["url"],
            "source": item["source"],
            "published_at": item["published_at"].isoformat(),
            "content_hash": item["content_hash"],
        }

    def save_many(self, items: list[dict]) -> int:
        rows = [self._to_row(item) for item in items]
        for offset in range(0, len(rows), self.batch_size):
            self.client.table(self.table_name).upsert(
                rows[offset : offset + self.batch_size],
                on_conflict="symbol,content_hash",
            ).execute()
        return len(rows)
