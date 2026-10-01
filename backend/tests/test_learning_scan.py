from datetime import date

import pandas as pd

from app.services.learning_memory import LearningMemory
from app.services.learning_scan import (
    scan_symbol_for_learning,
    scan_universe_for_learning,
)


def make_data():
    dates = pd.date_range("2025-09-24", periods=260, freq="B")
    close = [100.0] * 260
    close[-2] = 100.0
    close[-1] = 106.0

    return pd.DataFrame(
        {
            "Open": close,
            "High": [value + 1 for value in close],
            "Low": [value - 1 for value in close],
            "Close": close,
            "Volume": [1000.0] * 258 + [1200.0, 1500.0],
        },
        index=dates,
    )


def test_scan_symbol_ignores_5_percent_or_less(monkeypatch):
    data = make_data().copy()
    data.iloc[-1, data.columns.get_loc("Close")] = 105.0

    monkeypatch.setattr(
        "app.services.learning_scan.fetch_daily_data",
        lambda symbol, period: data,
    )

    result = scan_symbol_for_learning(
        "THYAO",
        data.index[-1].date(),
    )

    assert result is None


def test_scan_symbol_creates_event_above_5_percent(monkeypatch):
    data = make_data()

    monkeypatch.setattr(
        "app.services.learning_scan.fetch_daily_data",
        lambda symbol, period: data,
    )

    memory = LearningMemory()

    monkeypatch.setattr(
        "app.services.learning_scan.process_learning_event",
        lambda event, repository=None: memory.add(event) or True,
    )

    result = scan_symbol_for_learning(
        "THYAO",
        data.index[-1].date(),
    )

    assert result is not None
    assert result.rise_percent == 6.0
    assert result.reference_date == data.index[-2].date()
    assert memory.count() == 1


def test_scan_universe_continues_after_symbol_error(monkeypatch):
    def fake_scan(symbol, signal_date, repository=None):
        if symbol == "BAD":
            raise RuntimeError("data error")
        return None

    monkeypatch.setattr(
        "app.services.learning_scan.scan_symbol_for_learning",
        fake_scan,
    )

    result = scan_universe_for_learning(
        ["BAD", "THYAO"],
        date(2026, 9, 28),
    )

    assert result["scanned"] == 2
    assert result["events"] == 0
    assert len(result["errors"]) == 1
    assert result["errors"][0]["symbol"] == "BAD"
