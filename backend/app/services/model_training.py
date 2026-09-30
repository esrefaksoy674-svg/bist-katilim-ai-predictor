from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

from app.services.time_validation import (
    calculate_metrics,
    chronological_split,
)


@dataclass
class TrainedModel:
    model: Pipeline
    feature_names: list[str]
    sample_count: int
    metrics: dict


def _create_pipeline() -> Pipeline:
    return Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="median"),
            ),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=200,
                    random_state=42,
                    class_weight="balanced",
                    n_jobs=-1,
                ),
            ),
        ]
    )


def train_model(
    features: pd.DataFrame,
    targets: pd.Series,
    validation_ratio: float = 0.2,
) -> TrainedModel:
    """
    Zaman sırasını koruyarak model eğitir.

    Eski dönem:
        eğitim

    Daha sonraki dönem:
        doğrulama

    Böylece gelecekteki kayıtlar eğitim sırasında
    kullanılmaz.
    """

    if features.empty:
        raise ValueError(
            "Model eğitimi için özellik verisi boş."
        )

    if targets.empty:
        raise ValueError(
            "Model eğitimi için hedef verisi boş."
        )

    if len(features) != len(targets):
        raise ValueError(
            "Özellik ve hedef satır sayıları eşit olmalıdır."
        )

    if targets.nunique() < 2:
        raise ValueError(
            "Model eğitimi için en az iki sınıf gerekir."
        )

    (
        train_features,
        validation_features,
        train_targets,
        validation_targets,
    ) = chronological_split(
        features,
        targets,
        validation_ratio,
    )

    if train_targets.nunique() < 2:
        raise ValueError(
            "Eğitim bölümünde en az iki sınıf bulunmalıdır."
        )

    model = _create_pipeline()

    model.fit(
        train_features,
        train_targets,
    )

    validation_predictions = model.predict(
        validation_features
    )

    metrics = calculate_metrics(
        validation_targets,
        validation_predictions,
    )

    return TrainedModel(
        model=model,
        feature_names=list(features.columns),
        sample_count=len(train_features),
        metrics=metrics,
    )


def predict_probability(
    trained_model: TrainedModel,
    features: pd.DataFrame,
) -> list[float]:
    """
    >%5 yükseliş sınıfının olasılığını döndürür.
    """

    if features.empty:
        return []

    missing = set(
        trained_model.feature_names
    ) - set(features.columns)

    if missing:
        raise ValueError(
            "Tahmin verisinde eksik özellikler: "
            f"{sorted(missing)}"
        )

    ordered = features[
        trained_model.feature_names
    ]

    probabilities = (
        trained_model.model
        .predict_proba(ordered)[:, 1]
    )

    return [
        float(value)
        for value in probabilities
    ]
