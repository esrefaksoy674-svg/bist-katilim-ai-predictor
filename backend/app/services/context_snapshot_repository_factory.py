from app.services.context_snapshot_repository import ContextSnapshotRepository
from app.services.supabase_client import get_supabase_client


def get_context_snapshot_repository() -> ContextSnapshotRepository:
    return ContextSnapshotRepository(get_supabase_client())
