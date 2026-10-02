import numpy as np
import pandas as pd

from app.services.technical import calculate_features


def test_calculate_features_returns_expected_keys():
    periods = 260

    index = pd.date_range(
        "2025-01-01",
        periods=periods,
        freq="B",
    )

    close = np.linspace(
        100,
        150,
        periods,
    )

    data = pd.DataFrame(
        {
            "Open": close - 1,
            "High": close + 2,
            "Low": close - 2,
            "Close": close,
            "Volume": np.full(
                periods,
                1_000_000,
                dtype=float,
            ),
        },
        index=index,
    )

    result = calculate_features(data)

    expected_keys = {
        "rsi",
        "macd",
        "macd_signal",
        "macd_histogram",
        "vwap",
        "atr",
        "volume",
        "volume_avg20",
        "volume_ratio",
        "sma20",
        "sma50",
        "sma200",
        "momentum",
        "volatility",
        "price_vs_vwap_percent",
        "price_vs_sma20_percent",
        "price_vs_sma50_percent",
    }

    assert expected_keys.issubset(result.keys())


def test_calculate_features_rejects_empty_data():
    empty_data = pd.DataFrame()

    try:
        calculate_features(empty_data)
    except ValueError:
        return

    raise AssertionError(
        "Boş veri teknik analiz tarafından kabul edilmemeliydi."
    )


def test_calculate_features_handles_history_shorter_than_atr_window():
    periods = 11
    close = np.linspace(100, 110, periods)
    data = pd.DataFrame(
        {
            "Open": close - 1,
            "High": close + 2,
            "Low": close - 2,
            "Close": close,
            "Volume": np.full(periods, 1_000_000, dtype=float),
        },
        index=pd.date_range("2026-01-01", periods=periods, freq="B"),
    )

    result = calculate_features(data)

    assert result["atr"] is None
