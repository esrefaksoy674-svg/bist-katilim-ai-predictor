from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.services.model_registry import ModelRegistry, RegisteredModel


class ModelVersionRepository:
    def add(self, model: RegisteredModel) -> None:
        raise NotImplementedError

    def get(self, version: str) -> RegisteredModel | None:
        raise NotImplementedError

    def all(self) -> list[RegisteredModel]:
        raise NotImplementedError


class SupabaseModelVersionRepository(ModelVersionRepository):
    table_name = "model_versions"

    def __init__(self, client: Any):
        self.client = client

    @staticmethod
    def _to_row(model: RegisteredModel) -> dict:
        return {
            "version": model.version,
            "status": model.status,
            "accuracy": model.accuracy,
            "precision": model.precision,
            "recall": model.recall,
            "sample_count": model.sample_count,
            "pattern_count": model.pattern_count,
            "created_at": (
                model.created_at.isoformat()
                if model.created_at is not None
                else datetime.now(timezone.utc).isoformat()
            ),
            "activated_at": (
                model.activated_at.isoformat()
                if model.activated_at is not None
                else None
            ),
        }

    @staticmethod
    def _from_row(row: dict) -> RegisteredModel:
        def parse(value):
            if value is None:
                return None
            return datetime.fromisoformat(
                str(value).replace("Z", "+00:00")
            )

        return RegisteredModel(
            version=str(row["version"]),
            status=str(row["status"]),
            accuracy=row.get("accuracy"),
            precision=row.get("precision"),
            recall=row.get("recall"),
            sample_count=int(row.get("sample_count", 0)),
            pattern_count=int(row.get("pattern_count", 0)),
            created_at=parse(row.get("created_at")),
            activated_at=parse(row.get("activated_at")),
        )

    def add(self, model: RegisteredModel) -> None:
        self.client.table(self.table_name).upsert(
            self._to_row(model),
            on_conflict="version",
        ).execute()

    def get(self, version: str) -> RegisteredModel | None:
        response = (
            self.client.table(self.table_name)
            .select("*")
            .eq("version", version)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        return self._from_row(rows[0]) if rows else None

    def all(self) -> list[RegisteredModel]:
        response = (
            self.client.table(self.table_name)
            .select("*")
            .order("created_at")
            .execute()
        )
        return [self._from_row(row) for row in (response.data or [])]


def sync_registry(
    registry: ModelRegistry,
    repository: ModelVersionRepository,
) -> None:
    for model in registry.all():
        repository.add(model)
