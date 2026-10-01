from app.services.news_repository import SupabaseNewsRepository
from app.services.supabase_client import get_supabase_client


def get_news_repository() -> SupabaseNewsRepository:
    return SupabaseNewsRepository(get_supabase_client())
