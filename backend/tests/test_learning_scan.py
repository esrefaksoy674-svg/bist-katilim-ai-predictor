from datetime import date

import pandas as pd

from app.services.learning_memory import LearningMemory
from app.services.learning_scan import (
    scan_symbol_for_learning,
    scan_universe_for_learning,
)


def make_data():
    dates = pd.date_range("2026-09-24", periods=4, freq="B")
    return pd.DataFrame(
        {
            "Open": [100, 100, 100, 105],
            "High": [101, 101, 106, 111],
            "Low": [99, 99, 99, 104],
            "Close": [100, 100, 106, 110],
            "Volume": [1000, 1000, 1200, 1500],
        },
        index=dates,
    )


def test_scan_symbol_ignores_5_percent_or_less(monkeypatch):
    data = make_data().copy()
    data.loc[data.index[2], "Close"] = 105.0

    monkeypatch.setattr(
        "app.services.learning_scan.fetch_daily_data",
        lambda symbol, period: data,
    )

    result = scan_symbol_for_learning(
        "THYAO",
        data.index[2].date(),
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
        data.index[2].date(),
    )

    assert result is not None
    assert result.rise_percent == 6.0
    assert result.reference_date == data.index[1].date()
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
