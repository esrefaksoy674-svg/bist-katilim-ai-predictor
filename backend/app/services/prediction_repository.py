from __future__ import annotations

from datetime import date, datetime
from typing import Any

from app.models.prediction import Prediction


class PredictionRepository:
    def add(self, prediction: Prediction) -> None:
        raise NotImplementedError

    def get_by_date(self, prediction_date: date) -> list[Prediction]:
        raise NotImplementedError

    def get_latest_date(self) -> date | None:
        raise NotImplementedError

    def get_by_target_date(self, target_date: date) -> list[Prediction]:
        raise NotImplementedError

    def get_pending_through_date(self, target_date: date) -> list[Prediction]:
        raise NotImplementedError

    def get_recent(self, limit: int = 100) -> list[Prediction]:
        raise NotImplementedError


class SupabasePredictionRepository(PredictionRepository):
    table_name = "predictions"

    def __init__(self, client: Any):
        self.client = client

    @staticmethod
    def _to_row(prediction: Prediction) -> dict:
        return {
            "symbol": prediction.symbol.upper(),
            "prediction_date": prediction.prediction_date.isoformat(),
            "target_date": prediction.target_date.isoformat(),
            "probability_above_5": prediction.probability_above_5,
            "expected_change_percent": prediction.expected_change_percent,
            "model_confidence": prediction.model_confidence,
            "pattern_count": prediction.pattern_count,
            "explanation": prediction.explanation,
            "model_version": prediction.model_version,
            "actual_change_percent": prediction.actual_change_percent,
            "successful": prediction.successful,
            "evaluated_at": (
                prediction.evaluated_at.isoformat()
                if prediction.evaluated_at is not None
                else None
            ),
            "created_at": prediction.created_at.isoformat(),
        }

    @staticmethod
    def _from_row(row: dict) -> Prediction:
        def parse_datetime(value):
            if value is None:
                return None
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))

        return Prediction(
            symbol=str(row["symbol"]).upper(),
            prediction_date=date.fromisoformat(str(row["prediction_date"])),
            target_date=date.fromisoformat(str(row["target_date"])),
            probability_above_5=float(row["probability_above_5"]),
            expected_change_percent=float(row["expected_change_percent"]),
            model_confidence=float(row["model_confidence"]),
            pattern_count=int(row.get("pattern_count", 0)),
            explanation=row.get("explanation") or {},
            model_version=str(row["model_version"]),
            actual_change_percent=row.get("actual_change_percent"),
            successful=row.get("successful"),
            evaluated_at=parse_datetime(row.get("evaluated_at")),
            created_at=parse_datetime(row.get("created_at")),
        )

    def add(self, prediction: Prediction) -> None:
        self.client.table(self.table_name).upsert(
            self._to_row(prediction),
            on_conflict="symbol,prediction_date,model_version",
        ).execute()

    def get_latest_date(self) -> date | None:
        response = (
            self.client.table(self.table_name)
            .select("prediction_date")
            .order("prediction_date", desc=True)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        if not rows:
            return None
        return date.fromisoformat(str(rows[0]["prediction_date"]))

    def get_by_date(self, prediction_date: date) -> list[Prediction]:
        response = (
            self.client.table(self.table_name)
            .select("*")
            .eq("prediction_date", prediction_date.isoformat())
            .order("probability_above_5", desc=True)
            .execute()
        )
        return [self._from_row(row) for row in (response.data or [])]

    def get_by_target_date(self, target_date: date) -> list[Prediction]:
        response = (
            self.client.table(self.table_name)
            .select("*")
            .eq("target_date", target_date.isoformat())
            .order("probability_above_5", desc=True)
            .execute()
        )
        return [self._from_row(row) for row in (response.data or [])]

    def get_pending_through_date(self, target_date: date) -> list[Prediction]:
        response = (
            self.client.table(self.table_name)
            .select("*")
            .lte("target_date", target_date.isoformat())
            .is_("actual_change_percent", "null")
            .order("target_date")
            .order("probability_above_5", desc=True)
            .execute()
        )
        return [self._from_row(row) for row in (response.data or [])]

    def get_recent(self, limit: int = 100) -> list[Prediction]:
        safe_limit = max(1, min(int(limit), 500))
        response = (
            self.client.table(self.table_name)
            .select("*")
            .order("target_date", desc=True)
            .order("probability_above_5", desc=True)
            .limit(safe_limit)
            .execute()
        )
        return [self._from_row(row) for row in (response.data or [])]
