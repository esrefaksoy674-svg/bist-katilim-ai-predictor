from __future__ import annotations

from datetime import date, datetime, timezone

from app.services.prediction_repository import PredictionRepository
from app.services.market_data import fetch_daily_data


def evaluate_predictions_for_date(
    repository: PredictionRepository,
    prediction_date: date,
    target_date: date,
) -> int:
    """
    Hedef işlem günü kapandıktan sonra tahminleri gerçekleşen değişimle eşleştirir.

    Başarı ölçütü modelin hedefiyle aynıdır: gerçekleşen değişim > %5.
    """
    predictions = repository.get_by_date(prediction_date)
    evaluated = 0

    for prediction in predictions:
        if prediction.target_date != target_date:
            continue

        data = fetch_daily_data(prediction.symbol, period="2y")
        rows = data[data.index.date == target_date]
        previous_rows = data[data.index.date < target_date]

        if rows.empty or previous_rows.empty:
            continue

        current_close = float(rows.iloc[-1]["Close"])
        previous_close = float(previous_rows.iloc[-1]["Close"])
        if previous_close <= 0:
            continue

        actual_change = (current_close - previous_close) / previous_close * 100
        prediction.actual_change_percent = actual_change
        prediction.successful = actual_change > 5.0
        prediction.evaluated_at = datetime.now(timezone.utc)
        repository.add(prediction)
        evaluated += 1

    return evaluated
