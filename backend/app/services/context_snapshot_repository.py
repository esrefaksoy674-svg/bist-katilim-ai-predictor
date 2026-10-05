from __future__ import annotations

from typing import Any


class ContextSnapshotRepository:
    table_name = "context_snapshots"
    batch_size = 250

    def __init__(self, client: Any):
        self.client = client

    def save_many(self, snapshots: list[dict]) -> int:
        rows = [dict(row) for row in snapshots]
        for offset in range(0, len(rows), self.batch_size):
            self.client.table(self.table_name).upsert(
                rows[offset : offset + self.batch_size],
                on_conflict="symbol,available_date",
            ).execute()
        return len(rows)

    def all(self) -> list[dict]:
        rows = []
        offset = 0
        while True:
            response = (
                self.client.table(self.table_name)
                .select("*")
                .order("available_date")
                .range(offset, offset + self.batch_size - 1)
                .execute()
            )
            page = response.data or []
            rows.extend(page)
            if len(page) < self.batch_size:
                return rows
            offset += self.batch_size
