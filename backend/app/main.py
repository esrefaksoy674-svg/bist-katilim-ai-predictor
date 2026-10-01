from __future__ import annotations

from datetime import date

from fastapi import FastAPI, HTTPException

from app.core.health import get_health_status
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
        "universe_source": False,
    }
    errors = {}

    try:
        symbols = fetch_katilim_universe()
        checks["universe_source"] = bool(symbols)
    except Exception as exc:
        errors["universe_source"] = str(exc)

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
