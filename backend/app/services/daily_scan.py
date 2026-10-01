from __future__ import annotations

from datetime import date

from app.services.learning_runner import run_daily_learning
from app.services.model_registry import ModelRegistry
from app.services.prediction_repository_factory import get_prediction_repository
from app.services.runtime_model import load_active_model
from app.services.daily_prediction import run_daily_prediction
from app.services.universe import fetch_katilim_universe


def run_daily_scan(
    trading_date: date,
    history,
    learning_enabled: bool = True,
    top_n: int = 10,
):
    """Gün sonu öğrenme ve aktif modelle tahmin akışını birlikte çalıştırır."""
    symbols = fetch_katilim_universe()

    learning_result = None
    if learning_enabled:
        learning_result = run_daily_learning(
            symbols=symbols,
            signal_date=trading_date,
        )

    registry, _artifact = load_active_model()
    prediction_repository = get_prediction_repository()

    prediction_result = run_daily_prediction(
        prediction_date=trading_date,
        registry=registry,
        history=history,
        prediction_repository=prediction_repository,
        symbols=symbols,
        top_n=top_n,
    )

    return {
        "trading_date": trading_date.isoformat(),
        "universe_count": len(symbols),
        "learning": learning_result,
        "predictions": prediction_result,
    }
