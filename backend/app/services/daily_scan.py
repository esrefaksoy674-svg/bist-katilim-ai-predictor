from __future__ import annotations

from datetime import date

from app.core.config import settings
from app.services.context_snapshots import parse_sector_map
from app.services.context_snapshot_repository_factory import get_context_snapshot_repository
from app.services.daily_news import run_daily_news_collection
from app.services.prediction_evaluation import evaluate_predictions_for_target_date
from app.services.daily_prediction import run_daily_prediction
from app.services.learning_runner import run_daily_learning
from app.services.prediction_history import build_prediction_history
from app.services.prediction_repository_factory import get_prediction_repository
from app.services.runtime_model import load_active_model
from app.services.trading_calendar import next_trading_day
from app.services.universe import fetch_katilim_universe


def run_daily_scan(
    trading_date: date,
    learning_enabled: bool = True,
    top_n: int = 10,
):
    """Run end-of-day learning, news capture, and next-session predictions."""
    symbols = fetch_katilim_universe()
    if not symbols:
        raise RuntimeError("Günlük tarama için Katılım evreni boş.")

    target_date = next_trading_day(trading_date)
    prediction_repository = get_prediction_repository()
    evaluated_prediction_count = (
        evaluate_predictions_for_target_date(
            repository=prediction_repository,
            target_date=trading_date,
        )
        if hasattr(prediction_repository, "get_by_target_date")
        else 0
    )

    learning_result = None
    if learning_enabled:
        learning_result = run_daily_learning(
            symbols=symbols,
            signal_date=trading_date,
        )

    try:
        news_result = run_daily_news_collection(
            symbols=symbols,
            trading_date=trading_date,
        )
    except Exception as exc:
        # Keep an unavailable news store from cancelling the completed market scan.
        news_result = {
            "trading_date": trading_date.isoformat(),
            "source_count": 0,
            "reachable_sources": 0,
            "item_count": 0,
            "persisted_count": 0,
            "features_by_symbol": {},
            "error": type(exc).__name__,
        }

    context_status = {"status": "unavailable", "error": "RepositoryUnavailable"}
    try:
        context_repository = get_context_snapshot_repository()
        context_status = {"status": "pending"}
    except Exception as exc:
        context_repository = None
        context_status = {"status": "unavailable", "error": type(exc).__name__}

    registry, _artifact = load_active_model()
    history = build_prediction_history(
        symbols=symbols,
        prediction_date=trading_date,
    )
    prediction_result = run_daily_prediction(
        prediction_date=trading_date,
        target_date=target_date,
        registry=registry,
        history=history,
        prediction_repository=prediction_repository,
        symbols=symbols,
        top_n=top_n,
        context_snapshot_repository=context_repository,
        news_features_by_symbol=news_result.get("features_by_symbol", {}),
        sector_by_symbol=parse_sector_map(settings.sector_map),
        context_snapshot_status=context_status,
    )

    return {
        "trading_date": trading_date.isoformat(),
        "target_date": target_date.isoformat(),
        "universe_count": len(symbols),
        "learning": learning_result,
        "evaluated_prediction_count": evaluated_prediction_count,
        "predictions": prediction_result,
        "news": news_result,
        "context_snapshots": context_status,
    }
