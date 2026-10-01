import pandas as pd

from app.services.market_training_dataset import build_market_training_dataset


def make_data():
    dates = pd.date_range("2025-01-01", periods=205, freq="B")
    close = [100.0] * 205
    close[200] = 100.0
    close[201] = 106.0
    close[202] = 100.0
    close[203] = 103.0
    close[204] = 110.0

    return pd.DataFrame(
        {
            "Open": close,
            "High": [value + 1 for value in close],
            "Low": [value - 1 for value in close],
            "Close": close,
            "Volume": [1000.0] * 205,
        },
        index=dates,
    )


def test_market_training_dataset_contains_positive_and_baseline(monkeypatch):
    data = make_data()

    monkeypatch.setattr(
        "app.services.market_training_dataset.fetch_daily_data",
        lambda symbol, period: data,
    )

    features, targets = build_market_training_dataset(
        ["THYAO"],
        min_history=200,
    )

    assert len(features) == 4
    assert set(targets.tolist()) == {0, 1}
    assert "target" not in features.columns
    assert "actual_change_percent" not in features.columns


def test_market_training_dataset_respects_cutoff(monkeypatch):
    data = make_data()

    monkeypatch.setattr(
        "app.services.market_training_dataset.fetch_daily_data",
        lambda symbol, period: data,
    )

    cutoff = data.index[-1].date()

    features, targets = build_market_training_dataset(
        ["THYAO"],
        cutoff_date=cutoff,
        min_history=200,
    )

    assert len(features) == 3
    assert len(targets) == 3
