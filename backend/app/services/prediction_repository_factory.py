from __future__ import annotations

import os

from app.services.prediction_repository import SupabasePredictionRepository
from app.services.supabase_client import get_supabase_client


def get_prediction_repository():
    # Comparison deployment uses its own Render Postgres database.
    # Production deployments remain on the existing Supabase configuration.
    if os.getenv("DATABASE_URL"):
        from app.services.postgres_prediction_repository import PostgresPredictionRepository
        return PostgresPredictionRepository(os.environ["DATABASE_URL"])
    return SupabasePredictionRepository(get_supabase_client())
