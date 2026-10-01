from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.services.model_registry import ModelRegistry
from app.services.model_version_repository import (
    ModelVersionRepository,
    restore_registry,
    sync_registry,
)
from app.services.prediction_evaluation import evaluate_predictions_for_date
from app.services.prediction_repository import PredictionRepository


@dataclass(frozen=True)
class EvaluationRun:
    prediction_date: date
    target_date: date
    evaluated_count: int


def restore_models(
    registry: ModelRegistry,
    model_repository: ModelVersionRepository,
    artifact_repository=None,
) -> ModelRegistry:
    """Kalıcı model metadata ve artefaktlarını runtime registry'ye yükler."""
    return restore_registry(
        registry=registry,
        repository=model_repository,
        artifact_repository=artifact_repository,
    )


def persist_models(
    registry: ModelRegistry,
    model_repository: ModelVersionRepository,
) -> None:
    """Runtime model registry'sini kalıcı metadata ile senkronize eder."""
    sync_registry(
        registry=registry,
        repository=model_repository,
    )


def evaluate_daily_predictions(
    prediction_repository: PredictionRepository,
    prediction_date: date,
    target_date: date,
) -> EvaluationRun:
    """Hedef işlem günü kapandıktan sonra tahminleri değerlendirir."""
    count = evaluate_predictions_for_date(
        repository=prediction_repository,
        prediction_date=prediction_date,
        target_date=target_date,
    )
    return EvaluationRun(
        prediction_date=prediction_date,
        target_date=target_date,
        evaluated_count=count,
    )
