from __future__ import annotations

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from app.services.model_registry import ModelRegistry
from app.services.model_training_service import train_and_persist_market_model

MARKET_TIMEZONE = ZoneInfo("Europe/Istanbul")


def run_scheduled_training() -> dict:
    """İstanbul işlem günü sonrasında çalışacak günlük eğitim giriş noktası."""
    now = datetime.now(timezone.utc).astimezone(MARKET_TIMEZONE)
    version = f"daily-{now.strftime('%Y%m%d-%H%M%S')}"

    registry = ModelRegistry()
    result = train_and_persist_market_model(
        version=version,
        registry=registry,
        cutoff_date=now.date(),
        promote=True,
    )

    return {
        "status": "ok",
        "version": version,
        "date": now.date().isoformat(),
        "timezone": str(MARKET_TIMEZONE),
        "result": result,
    }


if __name__ == "__main__":
    print(run_scheduled_training())
