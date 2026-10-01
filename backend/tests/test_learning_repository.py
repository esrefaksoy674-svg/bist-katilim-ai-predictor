from app.services.learning_memory_repository import (
    SupabaseLearningEventRepository,
)
from app.services.learning_repository import get_learning_event_repository


def test_learning_repository_factory_uses_supabase(monkeypatch):
    fake_client = object()

    monkeypatch.setattr(
        "app.services.learning_repository.get_supabase_client",
        lambda: fake_client,
    )

    repository = get_learning_event_repository()

    assert isinstance(
        repository,
        SupabaseLearningEventRepository,
    )
    assert repository.client is fake_client
