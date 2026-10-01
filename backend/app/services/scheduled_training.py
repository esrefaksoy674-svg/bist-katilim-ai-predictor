from __future__ import annotations

from datetime import datetime, timezone

from app.services.model_persistence import restore_models
from app.services.model_registry import ModelRegistry
from app.services.model_repository import (
    get_model_artifact_repository,
    get_model_version_repository,
)
from app.services.model_training_service import train_and_persist_market_model

MARKET_TIMEZONE = __import__("zoneinfo").ZoneInfo("Europe/Istanbul")


def run_scheduled_training() -> dict:
    """Kalıcı aktif modeli yükleyip günlük aday modeli eğitir."""
    now = datetime.now(timezone.utc).astimezone(MARKET_TIMEZONE)
    version = f"daily-{now.strftime('%Y%m%d-%H%M%S')}"

    registry = ModelRegistry()
    restore_models(
        registry,
        get_model_version_repository(),
        get_model_artifact_repository(),
    )

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
        "active_model": (
            registry.active().version
            if registry.active() is not None
            else None
        ),
        "result": result,
    }


if __name__ == "__main__":
    print(run_scheduled_training())
