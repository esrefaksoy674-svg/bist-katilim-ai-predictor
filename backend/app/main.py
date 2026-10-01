from __future__ import annotations

from datetime import date

from fastapi import FastAPI, HTTPException

from app.core.health import (
    check_pipeline_imports,
    check_runtime_configuration,
    get_health_status,
)
from app.services.market_data import fetch_daily_data
from app.services.prediction_repository_factory import get_prediction_repository
from app.services.universe import fetch_katilim_universe

app = FastAPI(
    title="BIST Katılım AI Predictor",
    version="0.1.0",
    description="AI destekli BIST Katılım tahmin sistemi",
)


@app.get("/")
def root():
    return {
        "status": "ok",
        "application": "BIST Katılım AI Predictor",
        "version": "0.1.0",
    }


@app.get("/health")
def health():
    return get_health_status()


@app.get("/health/self-test")
def health_self_test():
    checks = {
        "api": True,
        "runtime_configuration": check_runtime_configuration(),
        "pipeline_imports": check_pipeline_imports(),
        "universe_source": False,
        "market_data_source": False,
        "persistence_read": False,
    }
    errors = {}

    read_only_checks = {
        "universe_source": fetch_katilim_universe,
        "market_data_source": lambda: fetch_daily_data("THYAO", period="5d"),
        "persistence_read": lambda: get_prediction_repository().get_by_date(date.today()),
    }

    for name, check in read_only_checks.items():
        try:
            result = check()
            if name == "persistence_read":
                checks[name] = result is not None
            elif hasattr(result, "empty"):
                checks[name] = not result.empty
            else:
                checks[name] = bool(result)
            if not checks[name]:
                errors[name] = "Dependency returned no usable data."
        except Exception as exc:
            # Exception text can include credentials or provider response details.
            errors[name] = {"type": type(exc).__name__}

    if not checks["runtime_configuration"]:
        errors["runtime_configuration"] = "Required application or Supabase configuration is missing or invalid."
    if not checks["pipeline_imports"]:
        errors["pipeline_imports"] = "One or more required pipeline packages are unavailable."

    status = "healthy" if all(checks.values()) else "degraded"

    return {
        "status": status,
        "checks": checks,
        "errors": errors,
    }


@app.get("/universe")
def universe():
    try:
        symbols = fetch_katilim_universe()
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Katılım evreni alınamadı: {exc}",
        ) from exc

    return {
        "trading_date": date.today().isoformat(),
        "count": len(symbols),
        "symbols": symbols,
    }


@app.get("/predictions")
def predictions(prediction_date: date | None = None):
    """Kalıcı tahmin kayıtlarını tarih bazında döndürür."""
    target_date = prediction_date or date.today()

    try:
        repository = get_prediction_repository()
        rows = repository.get_by_date(target_date)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Tahmin kayıtları alınamadı: {exc}",
        ) from exc

    return {
        "prediction_date": target_date.isoformat(),
        "count": len(rows),
        "predictions": [
            {
                "symbol": row.symbol,
                "target_date": row.target_date.isoformat(),
                "probability_above_5": row.probability_above_5,
                "expected_change_percent": row.expected_change_percent,
                "model_confidence": row.model_confidence,
                "pattern_count": row.pattern_count,
                "explanation": row.explanation,
                "model_version": row.model_version,
                "actual_change_percent": row.actual_change_percent,
                "successful": row.successful,
                "evaluated_at": (
                    row.evaluated_at.isoformat()
                    if row.evaluated_at is not None
                    else None
                ),
            }
            for row in rows
        ],
    }
