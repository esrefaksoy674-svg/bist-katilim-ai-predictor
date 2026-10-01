from __future__ import annotations

from datetime import date

from app.services.learning_control import learning_control
from app.services.model_persistence import persist_models
from app.services.model_repository import (
    get_model_artifact_repository,
    get_model_version_repository,
)
from app.services.model_registry import ModelRegistry
from app.services.persistent_training import train_from_market_history
from app.services.supabase_client import get_supabase_client
from app.services.universe import fetch_katilim_universe


def train_and_persist_market_model(
    version: str,
    registry: ModelRegistry,
    cutoff_date: date | None = None,
    validation_ratio: float = 0.2,
    promote: bool = True,
    min_history: int = 200,
):
    """Güncel Katılım evreniyle modeli eğitir ve kalıcı metadata/artefakt saklar."""
    if not learning_control.can_learn():
        raise RuntimeError("Öğrenme kapalıyken model eğitimi başlatılamaz.")

    symbols = fetch_katilim_universe()
    if not symbols:
        raise RuntimeError("Model eğitimi için Katılım evreni boş.")

    client = get_supabase_client()
    version_repository = get_model_version_repository()
    artifact_repository = get_model_artifact_repository()

    result = train_from_market_history(
        symbols=symbols,
        version=version,
        registry=registry,
        cutoff_date=cutoff_date,
        validation_ratio=validation_ratio,
        promote=promote,
        artifact_repository=artifact_repository,
        min_history=min_history,
    )

    persist_models(registry, version_repository)

    return result
