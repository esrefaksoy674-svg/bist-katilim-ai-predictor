from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline


@dataclass
class TrainedModel:
    model: Pipeline
    feature_names: list[str]
    sample_count: int


def train_model(
    features: pd.DataFrame,
    targets: pd.Series,
) -> TrainedModel:
    """
    >%5 yükseliş sınıflandırma modeli eğitir.

    targets:
        1 -> sonraki sonuç > %5
        0 -> değil

    Bu servis henüz modeli aktif hale getirmez.
    Eğitim sonucu daha sonra SHADOW model olarak
    değerlendirme katmanına gönderilecektir.
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

    clean_features = features.copy()

    feature_names = list(
        clean_features.columns
    )

    pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="median"
                ),
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

    pipeline.fit(
        clean_features,
        targets,
    )

    return TrainedModel(
        model=pipeline,
        feature_names=feature_names,
        sample_count=len(clean_features),
    )


def predict_probability(
    trained_model: TrainedModel,
    features: pd.DataFrame,
) -> list[float]:
    """
    Her kayıt için >%5 yükseliş olasılığını döndürür.
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
