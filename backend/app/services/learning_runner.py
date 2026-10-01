from __future__ import annotations

from datetime import date

from app.services.learning_repository import get_learning_event_repository
from app.services.learning_scan import scan_universe_for_learning


def run_daily_learning(
    symbols: list[str],
    signal_date: date,
    repository=None,
) -> dict:
    """
    Belirli bir işlem günü için kalıcı öğrenme taramasını çalıştırır.

    Repository açıkça verilmezse üretim Supabase repository'si kullanılır.
    Böylece günlük öğrenme RAM'de kaybolmaz. Aynı sembol ve işlem günü
    tekrar tarandığında repository'nin upsert kuralı mevcut kaydı günceller.
    """
    if repository is None:
        repository = get_learning_event_repository()

    return scan_universe_for_learning(
        symbols=symbols,
        signal_date=signal_date,
        repository=repository,
    )
