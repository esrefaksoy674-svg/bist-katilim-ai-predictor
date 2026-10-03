import pandas as pd

from app.services.training_examples import build_labeled_examples


def make_data(last_close=96.0):
    dates = pd.date_range("2025-01-01", periods=205, freq="B")
    close = [100.0] * 204 + [last_close]
    return pd.DataFrame(
        {
            "Open": close,
            "High": [x + 1 for x in close],
            "Low": [x - 1 for x in close],
            "Close": close,
            "Volume": [1000.0] * len(close),
        },
        index=dates,
    )


def test_examples_use_next_trading_day_as_target():
    data = make_data()
    result = build_labeled_examples(data, "THYAO")
    assert not result.empty
    last = result.iloc[-1]
    assert last["reference_date"] == data.index[-2].date()
    assert last["target_date"] == data.index[-1].date()
    assert last["actual_change_percent"] == -4.0
    assert last["target"] == 0


def test_five_percent_threshold_is_inclusive():
    data = make_data(last_close=105.0)
    result = build_labeled_examples(data, "THYAO")
    assert result.iloc[-1]["actual_change_percent"] == 5.0
    assert result.iloc[-1]["target"] == 1


def test_insufficient_history_returns_empty():
    data = make_data().iloc[:50]
    result = build_labeled_examples(data, "THYAO")
    assert result.empty
