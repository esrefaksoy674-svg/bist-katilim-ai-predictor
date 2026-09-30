from datetime import date

import pandas as pd
import pytest

from app.services.learning_pipeline import build_learning_event


def make_technical_data():
    index = pd.date_range(
        start="2026-01-01",
        periods=260,
        freq="B",
    )

    return pd.DataFrame(
        {
            "Open": [100.0] * 260,
            "High": [105.0] * 260,
            "Low": [95.0] * 260,
            "Close": [100.0] * 260,
            "Volume": [1000000.0] * 260,
        },
        index=index,
    )


def test_build_learning_event_uses_previous_trading_day(monkeypatch):
    reference_date = date(2026, 9, 25)
    signal_date = date(2026, 9, 28)

    monkeypatch.setattr(
        "app.services.learning_pipeline.get_reference_day",
        lambda symbol, signal_date: {
            "symbol": symbol,
            "signal_date": signal_date,
            "reference_date": reference_date,
            "close": 100.0,
        },
    )

    monkeypatch.setattr(
        "app.services.learning_pipeline.calculate_features",
        lambda data: {"rsi": 60.0},
    )

    event = build_learning_event(
        symbol="THYAO",
        signal_date=signal_date,
        signal_close=105.01,
        technical_data=make_technical_data(),
        technical_data_date=reference_date,
    )

    assert event is not None
    assert event.symbol == "THYAO"
    assert event.signal_date == signal_date
    assert event.reference_date == reference_date
    assert event.rise_percent == pytest.approx(5.01)
    assert event.technical_features == {"rsi": 60.0}


def test_future_technical_data_is_rejected(monkeypatch):
    reference_date = date(2026, 9, 25)
    signal_date = date(2026, 9, 28)
    future_date = date(2026, 9, 29)

    monkeypatch.setattr(
        "app.services.learning_pipeline.get_reference_day",
        lambda symbol, signal_date: {
            "symbol": symbol,
            "signal_date": signal_date,
            "reference_date": reference_date,
            "close": 100.0,
        },
    )

    with pytest.raises(ValueError, match="referans işlem gününe"):
        build_learning_event(
            symbol="THYAO",
            signal_date=signal_date,
            signal_close=105.01,
            technical_data=make_technical_data(),
            technical_data_date=future_date,
        )


def test_missing_technical_data_date_is_rejected(monkeypatch):
    reference_date = date(2026, 9, 25)
    signal_date = date(2026, 9, 28)

    monkeypatch.setattr(
        "app.services.learning_pipeline.get_reference_day",
        lambda symbol, signal_date: {
            "symbol": symbol,
            "signal_date": signal_date,
            "reference_date": reference_date,
            "close": 100.0,
        },
    )

    with pytest.raises(ValueError, match="Teknik verinin tarihi"):
        build_learning_event(
            symbol="THYAO",
            signal_date=signal_date,
            signal_close=105.01,
            technical_data=make_technical_data(),
        )
