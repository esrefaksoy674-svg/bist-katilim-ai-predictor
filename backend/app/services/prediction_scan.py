from __future__ import annotations

from datetime import date, datetime, timezone

import pandas as pd

from app.models.prediction import Prediction
from app.services.market_data import fetch_daily_data
from app.services.prediction_engine import FEATURE_NAMES, build_predictions
from app.services.prediction_repository import PredictionRepository
from app.services.technical import calculate_features


def build_candidate_features(
    symbols: list[str],
    prediction_date: date,
) -> pd.DataFrame:
    """Prediction gününe kadar bilinen veriden aday teknik özellikleri üretir."""
    rows = []

    for symbol in sorted(set(symbols)):
        data = fetch_daily_data(symbol, period="2y")
        history = data[data.index.date <= prediction_date]

        if history.empty:
            continue

        features = calculate_features(history)
        if any(features.get(name) is None for name in FEATURE_NAMES):
            continue

        row = dict(features)
        row["symbol"] = symbol.upper()
        rows.append(row)

    if not rows:
        return pd.DataFrame(columns=FEATURE_NAMES + ["symbol"])

    return pd.DataFrame(rows)


def run_prediction_scan(
    symbols: list[str],
    prediction_date: date,
    trained_model,
    model_version: str,
    history: pd.DataFrame,
    prediction_repository: PredictionRepository | None = None,
    top_n: int = 10,
    target_date: date | None = None,
) -> list[Prediction]:
    """Aktif modelle adayları tarar.

    target_date dışarıdan verilirse yalnızca bilinen takvim bilgisi olarak
    kullanılır. Piyasa verisinden gelecekteki işlem gününü okumaz; böylece
    geçmiş tarihli tahminlerde gelecek veri sızıntısı oluşmaz.
    """
    candidates = build_candidate_features(symbols, prediction_date)

    results = build_predictions(
        trained_model=trained_model,
        candidates=candidates,
        history=history,
        prediction_date=prediction_date,
        model_version=model_version,
        top_n=top_n,
    )

    resolved_target_date = target_date or prediction_date
    now = datetime.now(timezone.utc)
    predictions = []

    for result in results:
        prediction = Prediction(
            symbol=result.symbol,
            prediction_date=result.prediction_date,
            target_date=resolved_target_date,
            probability_above_5=result.probability_above_5,
            expected_change_percent=result.expected_change_percent,
            model_confidence=result.model_confidence,
            pattern_count=result.pattern_count,
            explanation=result.explanation,
            model_version=result.model_version,
            created_at=now,
        )
        predictions.append(prediction)

        if prediction_repository is not None:
            prediction_repository.add(prediction)

    return predictions
