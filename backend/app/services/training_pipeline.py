from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from app.services.learning_control import learning_control
from app.services.model_promotion import promote_if_better
from app.services.model_registry import ModelRegistry, RegisteredModel
from app.services.model_training import TrainedModel, train_model
from app.services.model_training_registry import register_trained_model


@dataclass(frozen=True)
class TrainingRunResult:
    version: str
    trained_model: TrainedModel
    registered_model: RegisteredModel
    promoted_model: RegisteredModel | None

    @property
    def active_model(self) -> RegisteredModel | None:
        return self.promoted_model


def train_shadow_model(
    features: pd.DataFrame,
    targets: pd.Series,
    version: str,
    registry: ModelRegistry,
    validation_ratio: float = 0.2,
    promote: bool = True,
    artifact_repository=None,
) -> TrainingRunResult:
    """
    Modeli eğitir ve önce SHADOW olarak kaydeder.

    Öğrenme kapalıysa model hiçbir şekilde ACTIVE yapılmaz.
    Öğrenme açıksa ve promote=True ise mevcut modelden daha iyi olduğu
    doğrulanan aday promote edilir.
    """
    trained = train_model(
        features,
        targets,
        validation_ratio=validation_ratio,
    )

    registered = register_trained_model(
        registry,
        version,
        trained,
    )
    registered.artifact = trained

    if artifact_repository is not None:
        artifact_repository.save(version, trained)

    promoted = None

    if promote and learning_control.can_learn():
        promoted = promote_if_better(
            registry,
            version,
        )

    return TrainingRunResult(
        version=version,
        trained_model=trained,
        registered_model=registered,
        promoted_model=promoted,
    )
