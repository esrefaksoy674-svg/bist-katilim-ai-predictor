from __future__ import annotations

import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score


def chronological_split(
    features: pd.DataFrame,
    targets: pd.Series,
    validation_ratio: float = 0.2,
):
    """
    Veriyi kronolojik sırayı koruyarak eğitim ve doğrulama
    bölümlerine ayırır.

    DatetimeIndex varsa veriler tarih sırasına göre güvenli biçimde
    sıralanır. Böylece çağıran kodun yanlış sırada veri vermesi
    geleceğin eğitim bölümüne sızmasına neden olmaz.
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

    working_features = features.copy()
    working_targets = targets.copy()

    if isinstance(working_features.index, pd.DatetimeIndex):
        if working_features.index.has_duplicates:
            raise ValueError(
                "Zaman bazlı doğrulamada yinelenen tarih indeksleri kullanılamaz."
            )

        order = working_features.index.argsort()
        working_features = working_features.iloc[order].copy()
        working_targets = working_targets.iloc[order].copy()

    split_index = int(
        len(working_features) * (1 - validation_ratio)
    )

    if split_index <= 0 or split_index >= len(working_features):
        raise ValueError(
            "Geçerli bir eğitim/doğrulama bölümü oluşturulamadı."
        )

    train_features = working_features.iloc[:split_index].copy()
    validation_features = working_features.iloc[split_index:].copy()
    train_targets = working_targets.iloc[:split_index].copy()
    validation_targets = working_targets.iloc[split_index:].copy()

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
            accuracy_score(actual, predicted)
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
