from __future__ import annotations

from app.services.learning_memory_repository import (
    LearningEventRepository,
    SupabaseLearningEventRepository,
)
from app.services.supabase_client import get_supabase_client


def get_learning_event_repository() -> LearningEventRepository:
    """Üretim öğrenme olayları için kalıcı Supabase repository'si döndürür."""
    return SupabaseLearningEventRepository(
        get_supabase_client()
    )
