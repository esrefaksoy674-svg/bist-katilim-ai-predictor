from __future__ import annotations

import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score


def chronological_split(
    features: pd.DataFrame,
    targets: pd.Series,
    validation_ratio: float = 0.2,
):
    """
    Veriyi zaman sırasını bozmadan eğitim ve doğrulama
    bölümlerine ayırır.

    Verinin zaten tarih sırasına göre sıralı olması gerekir.
    Gelecekteki kayıtlar eğitim bölümüne taşınmaz.
    """

    if len(features) != len(targets):
        raise ValueError(
            "Features ve targets aynı uzunlukta olmalıdır."
        )

    if len(features) < 10:
        raise ValueError(
            "Zaman bazlı doğrulama için en az 10 kayıt gerekir."
        )

    if not 0 < validation_ratio < 1:
        raise ValueError(
            "validation_ratio 0 ile 1 arasında olmalıdır."
        )

    split_index = int(
        len(features) * (1 - validation_ratio)
    )

    if split_index <= 0 or split_index >= len(features):
        raise ValueError(
            "Geçerli bir eğitim/doğrulama bölümü oluşturulamadı."
        )

    train_features = features.iloc[
        :split_index
    ].copy()

    validation_features = features.iloc[
        split_index:
    ].copy()

    train_targets = targets.iloc[
        :split_index
    ].copy()

    validation_targets = targets.iloc[
        split_index:
    ].copy()

    return (
        train_features,
        validation_features,
        train_targets,
        validation_targets,
    )


def calculate_metrics(
    actual,
    predicted,
) -> dict:
    """
    Model doğrulama metriklerini hesaplar.
    """

    return {
        "accuracy": float(
            accuracy_score(
                actual,
                predicted,
            )
        ),
        "precision": float(
            precision_score(
                actual,
                predicted,
                zero_division=0,
            )
        ),
        "recall": float(
            recall_score(
                actual,
                predicted,
                zero_division=0,
            )
        ),
        "sample_count": len(actual),
    }
