from __future__ import annotations

from datetime import date, datetime, timezone

from app.services.model_registry import ModelRegistry
from app.services.model_training_service import train_and_persist_market_model


def run_scheduled_training() -> dict:
    """Cloud scheduler tarafından çalıştırılacak günlük eğitim giriş noktası."""
    now = datetime.now(timezone.utc)
    version = f"daily-{now.strftime('%Y%m%d-%H%M%S')}"

    registry = ModelRegistry()
    result = train_and_persist_market_model(
        version=version,
        registry=registry,
        cutoff_date=date.today(),
        promote=True,
    )

    return {
        "status": "ok",
        "version": version,
        "date": date.today().isoformat(),
        "result": result,
    }


if __name__ == "__main__":
    print(run_scheduled_training())
