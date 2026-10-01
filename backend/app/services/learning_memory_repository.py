from __future__ import annotations

from datetime import date, datetime
from typing import Any

from app.models.learning_event import LearningEvent


class LearningEventRepository:
    """Kalıcı öğrenme olayları için repository sözleşmesi."""

    def add(self, event: LearningEvent) -> None:
        raise NotImplementedError

    def all(self) -> list[LearningEvent]:
        raise NotImplementedError

    def get_before(self, target_date: date) -> list[LearningEvent]:
        raise NotImplementedError


class SupabaseLearningEventRepository(LearningEventRepository):
    """LearningEvent kayıtlarını Supabase PostgreSQL'de saklar."""

    table_name = "learning_events"

    def __init__(self, client: Any):
        self.client = client

    @staticmethod
    def _to_row(event: LearningEvent) -> dict:
        return {
            "symbol": event.symbol.upper(),
            "signal_date": event.signal_date.isoformat(),
            "reference_date": event.reference_date.isoformat(),
            "rise_percent": event.rise_percent,
            "technical_features": event.technical_features,
            "news_features": event.news_features,
            "sector_features": event.sector_features,
            "source_quality": event.source_quality,
            "created_at": event.created_at.isoformat(),
        }

    @staticmethod
    def _from_row(row: dict) -> LearningEvent:
        return LearningEvent(
            symbol=str(row["symbol"]).upper(),
            signal_date=date.fromisoformat(row["signal_date"]),
            reference_date=date.fromisoformat(row["reference_date"]),
            rise_percent=float(row["rise_percent"]),
            technical_features=row.get("technical_features") or {},
            news_features=row.get("news_features") or {},
            sector_features=row.get("sector_features") or {},
            source_quality=row.get("source_quality"),
            created_at=datetime.fromisoformat(
                str(row["created_at"]).replace("Z", "+00:00")
            ),
        )

    def add(self, event: LearningEvent) -> None:
        self.client.table(self.table_name).upsert(
            self._to_row(event),
            on_conflict="symbol,signal_date",
        ).execute()

    def all(self) -> list[LearningEvent]:
        response = (
            self.client.table(self.table_name)
            .select("*")
            .order("signal_date")
            .execute()
        )
        return [self._from_row(row) for row in (response.data or [])]

    def get_before(self, target_date: date) -> list[LearningEvent]:
        response = (
            self.client.table(self.table_name)
            .select("*")
            .lt("signal_date", target_date.isoformat())
            .order("signal_date")
            .execute()
        )
        return [self._from_row(row) for row in (response.data or [])]
