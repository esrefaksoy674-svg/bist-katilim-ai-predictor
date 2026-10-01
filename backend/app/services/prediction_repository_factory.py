from __future__ import annotations

from app.services.prediction_repository import SupabasePredictionRepository
from app.services.supabase_client import get_supabase_client


def get_prediction_repository():
    return SupabasePredictionRepository(get_supabase_client())
