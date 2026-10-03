from __future__ import annotations

import secrets
from datetime import date, datetime, timezone
from pathlib import Path
from time import perf_counter

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.health import (
    check_pipeline_imports,
    check_runtime_configuration,
    get_health_status,
)
from app.services.market_data import fetch_daily_data
from app.services.news_ingestion import collect_configured_news
from app.services.prediction_repository_factory import get_prediction_repository
from app.services.trading_calendar import next_trading_day
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


@app.get("/dashboard", include_in_schema=False)
def dashboard():
    """Serve the same-origin, static predictions dashboard."""
    dashboard_file = Path(__file__).parent / "static" / "dashboard.html"
    return FileResponse(dashboard_file, media_type="text/html; charset=utf-8")


@app.get("/manifest.webmanifest", include_in_schema=False)
def pwa_manifest():
    return FileResponse(
        Path(__file__).parent / "static" / "manifest.webmanifest",
        media_type="application/manifest+json",
    )


@app.get("/app-icon.svg", include_in_schema=False)
def pwa_icon():
    return FileResponse(
        Path(__file__).parent / "static" / "app-icon.svg",
        media_type="image/svg+xml",
    )


@app.get("/service-worker.js", include_in_schema=False)
def service_worker():
    return FileResponse(
        Path(__file__).parent / "static" / "service-worker.js",
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"},
    )


@app.get("/health")
def health():
    return get_health_status()


@app.get("/health/self-test")
def health_self_test(x_self_test_token: str | None = Header(default=None)):
    """Run protected, read-only checks for API and critical pipeline dependencies."""
    expected_token = settings.self_test_token
    if not expected_token.strip():
        raise HTTPException(
            status_code=503,
            detail="Self-test access is not configured.",
        )
    if x_self_test_token is None or not secrets.compare_digest(
        x_self_test_token,
        expected_token,
    ):
        raise HTTPException(status_code=401, detail="Unauthorized.")

    started = perf_counter()
    checked_at = datetime.now(timezone.utc).isoformat()
    checks = {
        "api": True,
        "runtime_configuration": check_runtime_configuration(),
        "pipeline_imports": check_pipeline_imports(),
        "universe_source": False,
        "market_data_source": False,
        "persistence_read": False,
    }
    errors = {}

    # These probes only fetch source data or read existing predictions; they never
    # create, update, or delete application data.
    read_only_checks = {
        "universe_source": fetch_katilim_universe,
        "market_data_source": lambda: fetch_daily_data("THYAO", period="5d"),
        "persistence_read": lambda: get_prediction_repository().get_by_date(date.today()),
    }
    check_durations_ms = {}

    for name, check in read_only_checks.items():
        check_started = perf_counter()
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
            errors[name] = {"type": type(exc).__name__}
        finally:
            check_durations_ms[name] = round((perf_counter() - check_started) * 1000, 2)

    if not checks["runtime_configuration"]:
        errors["runtime_configuration"] = (
            "Required application or Supabase configuration is missing or invalid."
        )
    if not checks["pipeline_imports"]:
        errors["pipeline_imports"] = "One or more required pipeline packages are unavailable."

    status = "healthy" if all(checks.values()) else "degraded"
    return {
        "status": status,
        "checked_at": checked_at,
        "duration_ms": round((perf_counter() - started) * 1000, 2),
        "checks": checks,
        "check_durations_ms": check_durations_ms,
        "errors": errors,
    }


@app.get("/news")
def news(symbol: str | None = None):
    """Fetch configured RSS sources and return quality-checked news items."""
    try:
        symbols = [symbol.upper()] if symbol else []
        return collect_configured_news(symbols)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Haber kaynakları kullanılamıyor: {type(exc).__name__}",
        ) from exc


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


@app.get("/performance")
def performance(limit: int = 100):
    """Summarize recorded forecast outcomes and return recent tracking history."""
    try:
        rows = get_prediction_repository().get_recent(limit=limit)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Tahmin sonuçları alınamadı: {type(exc).__name__}",
        ) from exc

    evaluated = [row for row in rows if row.actual_change_percent is not None]
    successful_count = sum(
        1 for row in evaluated if row.actual_change_percent >= 5.0
    )
    average_actual_change = (
        sum(row.actual_change_percent for row in evaluated) / len(evaluated)
        if evaluated else None
    )
    return {
        "tracked_count": len(rows),
        "evaluated_count": len(evaluated),
        "pending_count": len(rows) - len(evaluated),
        "successful_count": successful_count,
        "hit_rate_percent": (
            round(successful_count / len(evaluated) * 100, 2)
            if evaluated else None
        ),
        "average_actual_change_percent": (
            round(average_actual_change, 2)
            if average_actual_change is not None else None
        ),
        "predictions": [
            {
                "symbol": row.symbol,
                "prediction_date": row.prediction_date.isoformat(),
                "target_date": row.target_date.isoformat(),
                "probability_above_5": row.probability_above_5,
                "expected_change_percent": row.expected_change_percent,
                "actual_change_percent": row.actual_change_percent,
                "successful": (
                    row.actual_change_percent >= 5.0
                    if row.actual_change_percent is not None else None
                ),
                "model_version": row.model_version,
            }
            for row in rows
        ],
    }


@app.get("/predictions")
def predictions(prediction_date: date | None = None):
    """Return next-session forecasts ranked by estimated probability of +5%."""
    try:
        repository = get_prediction_repository()
        target_date = prediction_date
        if target_date is None:
            target_date = repository.get_latest_date() or date.today()
        rows = repository.get_by_date(target_date)
        next_session = next_trading_day(target_date)
        rows = [
            row
            for row in rows
            if row.target_date == next_session
        ]
        rows.sort(
            key=lambda row: (
                row.probability_above_5,
                row.expected_change_percent,
                row.model_confidence,
                row.pattern_count,
            ),
            reverse=True,
        )
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
