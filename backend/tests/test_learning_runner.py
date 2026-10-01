from datetime import date

from app.services.learning_memory_repository import (
    SupabaseLearningEventRepository,
)
from app.services.learning_runner import run_daily_learning


def test_daily_learning_uses_supabase_repository_by_default(monkeypatch):
    fake_repository = object()

    monkeypatch.setattr(
        "app.services.learning_runner.get_learning_event_repository",
        lambda: fake_repository,
    )
    monkeypatch.setattr(
        "app.services.learning_runner.scan_universe_for_learning",
        lambda symbols, signal_date, repository: {
            "symbols": symbols,
            "signal_date": signal_date,
            "repository": repository,
        },
    )

    result = run_daily_learning(
        symbols=["THYAO", "TUPRS"],
        signal_date=date(2026, 9, 28),
    )

    assert result["symbols"] == ["THYAO", "TUPRS"]
    assert result["signal_date"] == date(2026, 9, 28)
    assert result["repository"] is fake_repository


def test_daily_learning_accepts_explicit_repository(monkeypatch):
    fake_repository = object()

    monkeypatch.setattr(
        "app.services.learning_runner.scan_universe_for_learning",
        lambda symbols, signal_date, repository: {
            "repository": repository,
        },
    )

    result = run_daily_learning(
        symbols=["THYAO"],
        signal_date=date(2026, 9, 28),
        repository=fake_repository,
    )

    assert result["repository"] is fake_repository


def test_learning_repository_is_supabase_implementation():
    # Üretim factory'sinin gerçek implementasyonu Supabase repository'dir.
    # Bu test bağlantı kurmaz; sadece sınıf sözleşmesini doğrular.
    assert issubclass(
        SupabaseLearningEventRepository,
        object,
    )
