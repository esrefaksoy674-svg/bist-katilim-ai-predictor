import pandas as pd

from app.services.training_examples import build_labeled_examples


def make_data():
    dates = pd.date_range("2025-01-01", periods=205, freq="B")
    close = [100.0] * 203 + [106.0, 102.0]
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
    result = build_labeled_examples(make_data(), "THYAO")
    assert not result.empty
    last = result.iloc[-1]
    assert last["reference_date"] == make_data().index[-2].date()
    assert last["target_date"] == make_data().index[-1].date()
    assert last["actual_change_percent"] == -4.0
    assert last["target"] == 0


def test_strict_five_percent_threshold_is_applied():
    data = make_data()
    data.iloc[-1, data.columns.get_loc("Close")] = 105.01
    result = build_labeled_examples(data, "THYAO")
    assert result.iloc[-1]["target"] == 1


def test_insufficient_history_returns_empty():
    data = make_data().iloc[:50]
    result = build_labeled_examples(data, "THYAO")
    assert result.empty
