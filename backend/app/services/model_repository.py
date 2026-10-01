from __future__ import annotations

from app.services.model_artifact_repository import (
    SupabaseStorageModelArtifactRepository,
)
from app.services.model_version_repository import SupabaseModelVersionRepository
from app.services.supabase_client import get_supabase_client


def get_model_version_repository():
    return SupabaseModelVersionRepository(get_supabase_client())


def get_model_artifact_repository():
    return SupabaseStorageModelArtifactRepository(get_supabase_client())
