from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from math import sqrt

import pandas as pd

from app.services.model_training import TrainedModel, predict_probability


FEATURE_NAMES = [
    "rsi",
    "macd",
    "macd_signal",
    "macd_histogram",
    "vwap",
    "atr",
    "volume",
    "volume_avg20",
    "volume_ratio",
    "sma20",
    "sma50",
    "sma200",
    "momentum",
    "volatility",
    "price_vs_vwap_percent",
    "price_vs_sma20_percent",
    "price_vs_sma50_percent",
]


@dataclass(frozen=True)
class PredictionCandidate:
    symbol: str
    prediction_date: date
    probability_above_5: float
    expected_change_percent: float
    model_confidence: float
    pattern_count: int
    explanation: dict
    model_version: str

    def to_dict(self) -> dict:
        return asdict(self)


def build_training_matrix(examples: pd.DataFrame):
    """Pozitif/negatif örneklerden yalnızca model özelliklerini çıkarır."""
    if examples is None or examples.empty:
        raise ValueError("Model eğitim örnekleri boş.")

    missing = set(FEATURE_NAMES + ["target"]) - set(examples.columns)
    if missing:
        raise ValueError(
            f"Model eğitim örneklerinde eksik alanlar: {sorted(missing)}"
        )

    working = examples.copy()
    index = pd.to_datetime(working["reference_date"])
    features = working[FEATURE_NAMES].copy()
    targets = working["target"].astype(int).copy()
    features.index = index
    targets.index = index
    return features, targets


def _similar_examples(
    candidate: pd.Series,
    history: pd.DataFrame,
    limit: int = 20,
) -> pd.DataFrame:
    if history is None or history.empty:
        return pd.DataFrame()

    required = set(FEATURE_NAMES + ["actual_change_percent", "target"])
    if not required.issubset(history.columns):
        return pd.DataFrame()

    base = history[FEATURE_NAMES].apply(pd.to_numeric, errors="coerce")
    row = pd.to_numeric(candidate[FEATURE_NAMES], errors="coerce")
    medians = base.median().replace(0, 1.0)
    scale = base.std().replace(0, 1.0).fillna(1.0)

    distances = ((base - row) / scale).pow(2).sum(axis=1).pow(0.5)
    result = history.copy()
    result["_distance"] = distances
    return result.sort_values("_distance").head(limit)


def build_predictions(
    trained_model: TrainedModel,
    candidates: pd.DataFrame,
    history: pd.DataFrame,
    prediction_date: date,
    model_version: str,
    top_n: int = 10,
) -> list[PredictionCandidate]:
    """Modeli kullanarak istatistiksel tahmin kayıtları üretir.

    probability_above_5 model olasılığıdır.
    expected_change_percent benzer geçmiş örneklerin gerçekleşmiş değişimlerinden
    türetilen istatistiksel beklentidir.
    model_confidence doğrulama başarımından ayrı bir olasılık değildir; burada
    doğrulama accuracy değeri ayrı bir kalite göstergesi olarak taşınır.
    """
    if candidates is None or candidates.empty:
        return []

    missing = set(FEATURE_NAMES + ["symbol"]) - set(candidates.columns)
    if missing:
        raise ValueError(
            f"Tahmin adaylarında eksik alanlar: {sorted(missing)}"
        )

    probabilities = predict_probability(
        trained_model,
        candidates[FEATURE_NAMES],
    )

    validation_accuracy = float(
        trained_model.metrics.get("accuracy", 0.0)
    )
    rows: list[PredictionCandidate] = []

    for position, (_, candidate) in enumerate(candidates.iterrows()):
        probability = float(probabilities[position])
        similar = _similar_examples(candidate, history)

        if similar.empty:
            expected_change = 0.0
            pattern_count = 0
            positive_rate = 0.0
        else:
            expected_change = float(
                pd.to_numeric(
                    similar["actual_change_percent"],
                    errors="coerce",
                ).dropna().mean()
            )
            pattern_count = int(len(similar))
            positive_rate = float(
                pd.to_numeric(
                    similar["target"],
                    errors="coerce",
                ).mean()
            )

        rows.append(
            PredictionCandidate(
                symbol=str(candidate["symbol"]).upper(),
                prediction_date=prediction_date,
                probability_above_5=max(0.0, min(1.0, probability)),
                expected_change_percent=expected_change,
                model_confidence=max(
                    0.0, min(1.0, validation_accuracy)
                ),
                pattern_count=pattern_count,
                explanation={
                    "validation_accuracy": validation_accuracy,
                    "historical_similar_positive_rate": positive_rate,
                    "similar_sample_count": pattern_count,
                    "method": "random_forest_plus_similarity_statistics",
                },
                model_version=model_version,
            )
        )

    rows.sort(
        key=lambda item: (
            item.probability_above_5,
            item.model_confidence,
            item.pattern_count,
        ),
        reverse=True,
    )
    return rows[:top_n]
