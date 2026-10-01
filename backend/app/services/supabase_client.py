from __future__ import annotations

from supabase import Client, create_client

from app.core.config import settings


def get_supabase_client() -> Client:
    if not settings.supabase_url or not settings.supabase_key:
        raise RuntimeError(
            "Supabase bağlantısı için SUPABASE_URL ve SUPABASE_KEY ayarlanmalıdır."
        )

    return create_client(
        settings.supabase_url,
        settings.supabase_key,
    )
