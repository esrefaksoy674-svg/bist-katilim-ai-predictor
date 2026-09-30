from datetime import date

import pandas as pd

from app.services.learning_pipeline import (
    build_learning_event,
)


def test_learning_pipeline_uses_reference_day(
    monkeypatch,
):
    reference = {
        "symbol": "THYAO",
        "signal_date": date(2026, 9, 28),
        "reference_date": date(2026, 9, 25),
        "open": 100.0,
        "high": 104.0,
        "low": 99.0,
        "close": 100.0,
        "volume": 1_000_000.0,
    }

    captured = {}

    def fake_reference_day(
        symbol,
        signal_date,
    ):
        return reference

    def fake_calculate_features(data):
        captured["data"] = data
        return {
            "rsi": 55.0,
            "macd": 1.0,
        }

    monkeypatch.setattr(
        "app.services.learning_pipeline.get_reference_day",
        fake_reference_day,
    )

    monkeypatch.setattr(
        "app.services.learning_pipeline.calculate_features",
        fake_calculate_features,
    )

    technical_data = pd.DataFrame(
        {
            "Open": [99.0, 100.0],
            "High": [101.0, 102.0],
            "Low": [98.0, 99.0],
            "Close": [100.0, 100.0],
            "Volume": [900_000.0, 1_000_000.0],
        }
    )

    event = build_learning_event(
        symbol="THYAO",
        signal_date=date(2026, 9, 28),
        signal_close=105.01,
        technical_data=technical_data,
    )

    assert event is not None
    assert event.reference_date == date(2026, 9, 25)
    assert event.signal_date == date(2026, 9, 28)
    assert event.rise_percent == 5.01

    assert captured["data"] is technical_data
    assert event.technical_features["rsi"] == 55.0
