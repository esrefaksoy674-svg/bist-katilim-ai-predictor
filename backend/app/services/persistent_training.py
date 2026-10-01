from __future__ import annotations

from app.services.learning_dataset import events_to_dataset
from app.services.learning_repository import get_learning_event_repository
from app.services.model_registry import ModelRegistry
from app.services.training_pipeline import TrainingRunResult, train_shadow_model


def train_from_learning_memory(
    version: str,
    registry: ModelRegistry,
    repository=None,
    validation_ratio: float = 0.2,
    promote: bool = True,
    artifact_repository=None,
) -> TrainingRunResult:
    """
    Kalıcı öğrenme hafızasındaki olaylardan model eğitimi başlatır.

    Yalnızca daha önce kaydedilmiş öğrenme olaylarını kullanır. Veri yetersiz
    veya tek sınıflıysa RandomForest eğitimini zorlamaz; açık bir hata verir.
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
            "Yalnızca >%5 öğrenme olayları tek başına yeterli değildir; "
            "negatif/baseline örnekleri de toplanmalıdır."
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
