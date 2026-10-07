from __future__ import annotations

from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

from app.services.prediction_repository import PredictionRepository
from app.services.market_data import fetch_daily_data

MARKET_TIMEZONE = ZoneInfo("Europe/Istanbul")
MARKET_CLOSE = time(18, 0)


def _session_is_closed(target_date: date) -> bool:
    """Do not lock in an intraday result as the final daily outcome."""
    now_local = datetime.now(MARKET_TIMEZONE)
    if target_date < now_local.date():
        return True
    if target_date > now_local.date():
        return False
    return now_local.time() >= MARKET_CLOSE


def evaluate_predictions_for_date(
    repository: PredictionRepository,
    prediction_date: date,
    target_date: date,
) -> int:
    """
    Hedef işlem günü kapandıktan sonra tahminleri gerçekleşen değişimle eşleştirir.

    Başarı ölçütü modelin hedefiyle aynıdır: gerçekleşen değişim >= %5.
    """
    predictions = repository.get_by_date(prediction_date)
    return _evaluate_predictions(repository, predictions, target_date)


def evaluate_predictions_for_target_date(
    repository: PredictionRepository,
    target_date: date,
) -> int:
    """Evaluate unresolved predictions whose target sessions have closed."""
    if hasattr(repository, "get_pending_through_date"):
        predictions = repository.get_pending_through_date(target_date)
    else:
        predictions = repository.get_by_target_date(target_date)
    return _evaluate_predictions(repository, predictions, target_date)


def _evaluate_predictions(repository, predictions, through_date: date) -> int:
    evaluated = 0

    for prediction in predictions:
        prediction_target_date = prediction.target_date
        if prediction_target_date > through_date:
            continue

        # A target that is still trading must never be evaluated from a partial
        # intraday close. Once today's session is closed, an earlier provisional
        # value is allowed to be corrected with the final daily close.
        if not _session_is_closed(prediction_target_date):
            continue
        if (
            prediction.actual_change_percent is not None
            and prediction_target_date < date.today()
        ):
            continue

        data = fetch_daily_data(prediction.symbol, period="2y")
        rows = data[data.index.date == prediction_target_date]
        previous_rows = data[data.index.date < prediction_target_date]

        if rows.empty or previous_rows.empty:
            continue

        current_close = float(rows.iloc[-1]["Close"])
        previous_close = float(previous_rows.iloc[-1]["Close"])
        if previous_close <= 0:
            continue

        actual_change = (current_close - previous_close) / previous_close * 100
        prediction.actual_change_percent = actual_change
        prediction.successful = actual_change >= 5.0
        prediction.evaluated_at = datetime.now(timezone.utc)
        repository.add(prediction)
        evaluated += 1

    return evaluated
