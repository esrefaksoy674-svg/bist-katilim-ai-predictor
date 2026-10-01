from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class RegisteredModel:
    version: str
    status: str
    accuracy: float | None = None
    precision: float | None = None
    recall: float | None = None
    sample_count: int = 0
    pattern_count: int = 0
    created_at: datetime | None = None
    activated_at: datetime | None = None
    artifact: object | None = None


class ModelRegistry:
    """Aktif, gölge ve arşiv modellerin yaşam döngüsünü yönetir."""

    def __init__(self):
        self._models: dict[str, RegisteredModel] = {}
        self._active_version: str | None = None

    def register_shadow(
        self,
        version: str,
        accuracy: float | None = None,
        precision: float | None = None,
        recall: float | None = None,
        sample_count: int = 0,
        pattern_count: int = 0,
        artifact: object | None = None,
    ) -> RegisteredModel:
        if version in self._models:
            raise ValueError(f"Model sürümü zaten kayıtlı: {version}")

        model = RegisteredModel(
            version=version,
            status="SHADOW",
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            sample_count=sample_count,
            pattern_count=pattern_count,
            created_at=datetime.now(timezone.utc),
            artifact=artifact,
        )
        self._models[version] = model
        return model

    def get(self, version: str) -> RegisteredModel | None:
        return self._models.get(version)

    def active(self) -> RegisteredModel | None:
        if self._active_version is None:
            return None
        return self._models.get(self._active_version)

    def activate(self, version: str) -> RegisteredModel:
        model = self._models.get(version)

        if model is None:
            raise ValueError(f"Model bulunamadı: {version}")

        if model.status != "SHADOW":
            raise ValueError("Yalnızca SHADOW model aktif edilebilir.")

        if self._active_version is not None:
            old_model = self._models[self._active_version]
            old_model.status = "ARCHIVED"

        model.status = "ACTIVE"
        model.activated_at = datetime.now(timezone.utc)
        self._active_version = version
        return model

    def rollback(self, version: str) -> RegisteredModel:
        """Belirtilen arşiv modeli tekrar aktif eder."""
        target = self._models.get(version)

        if target is None:
            raise ValueError(f"Model bulunamadı: {version}")

        if target.status != "ARCHIVED":
            raise ValueError("Rollback yalnızca ARCHIVED modele yapılabilir.")

        current = self.active()
        if current is not None:
            current.status = "ARCHIVED"

        target.status = "ACTIVE"
        target.activated_at = datetime.now(timezone.utc)
        self._active_version = version
        return target

    def all(self) -> list[RegisteredModel]:
        return list(self._models.values())


model_registry = ModelRegistry()
