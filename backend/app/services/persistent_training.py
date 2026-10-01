from __future__ import annotations

from datetime import date

from app.services.learning_dataset import events_to_dataset
from app.services.learning_repository import get_learning_event_repository
from app.services.market_training_dataset import build_market_training_dataset
from app.services.model_registry import ModelRegistry
from app.services.training_pipeline import TrainingRunResult, train_shadow_model


def train_from_market_history(
    symbols: list[str],
    version: str,
    registry: ModelRegistry,
    cutoff_date: date | None = None,
    validation_ratio: float = 0.2,
    promote: bool = True,
    artifact_repository=None,
    min_history: int = 200,
) -> TrainingRunResult:
    """Katılım piyasa geçmişinden pozitif/negatif örneklerle model eğitir."""
    features, targets = build_market_training_dataset(
        symbols=symbols,
        cutoff_date=cutoff_date,
        min_history=min_history,
    )

    return train_shadow_model(
        features=features,
        targets=targets,
        version=version,
        registry=registry,
        validation_ratio=validation_ratio,
        promote=promote,
        artifact_repository=artifact_repository,
    )


def train_from_learning_memory(
    version: str,
    registry: ModelRegistry,
    repository=None,
    validation_ratio: float = 0.2,
    promote: bool = True,
    artifact_repository=None,
) -> TrainingRunResult:
    """
    Kalıcı >%5 öğrenme olaylarından model eğitimi başlatır.

    Bu yol yalnızca pozitif olay hafızasını kullanır. Üretim modelinin
    iki sınıflı eğitimi için train_from_market_history tercih edilir.
    """
    if repository is None:
        repository = get_learning_event_repository()

    events = repository.all()
    features, targets = events_to_dataset(events)

    if features.empty:
        raise ValueError("Model eğitimi için kalıcı öğrenme verisi bulunamadı.")

    if targets.nunique() < 2:
        raise ValueError(
            "Model eğitimi için en az iki hedef sınıf gerekir. "
            "Pozitif öğrenme olayları tek başına yeterli değildir."
        )

    return train_shadow_model(
        features=features,
        targets=targets,
        version=version,
        registry=registry,
        validation_ratio=validation_ratio,
        promote=promote,
        artifact_repository=artifact_repository,
    )
