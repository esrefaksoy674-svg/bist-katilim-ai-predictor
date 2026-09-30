from __future__ import annotations

from app.services.model_registry import (
    ModelRegistry,
    RegisteredModel,
)
from app.services.model_training import (
    TrainedModel,
)


def register_trained_model(
    registry: ModelRegistry,
    version: str,
    trained_model: TrainedModel,
) -> RegisteredModel:
    """
    Eğitilmiş modeli SHADOW olarak registry'ye kaydeder.

    Model burada aktif edilmez.
    """

    metrics = trained_model.metrics

    return registry.register_shadow(
        version=version,
        accuracy=metrics.get("accuracy"),
        precision=metrics.get("precision"),
        recall=metrics.get("recall"),
        sample_count=trained_model.sample_count,
    )
