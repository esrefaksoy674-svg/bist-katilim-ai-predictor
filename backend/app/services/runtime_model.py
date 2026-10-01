from __future__ import annotations

from app.services.model_artifact_repository import (
    SupabaseStorageModelArtifactRepository,
)
from app.services.model_registry import ModelRegistry
from app.services.model_version_repository import (
    SupabaseModelVersionRepository,
    restore_registry,
)
from app.services.supabase_client import get_supabase_client


def load_active_model() -> tuple[ModelRegistry, object]:
    """Supabase'tan kayıtlı aktif model metadata ve artefaktını yükler."""
    client = get_supabase_client()
    registry = ModelRegistry()
    repository = SupabaseModelVersionRepository(client)
    artifact_repository = SupabaseStorageModelArtifactRepository(client)

    restore_registry(
        registry=registry,
        repository=repository,
        artifact_repository=artifact_repository,
    )

    active = registry.active()
    if active is None:
        raise RuntimeError("Kalıcı aktif model bulunamadı.")

    if active.artifact is None:
        raise RuntimeError(
            f"Aktif model artefaktı yüklenemedi: {active.version}"
        )

    return registry, active.artifact
