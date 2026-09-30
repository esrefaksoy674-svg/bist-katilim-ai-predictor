import pandas as pd

from app.services.technical import calculate_features


def test_missing_ohlcv_column_is_rejected():
    data = pd.DataFrame(
        {
            "Open": [100, 101, 102],
            "High": [103, 104, 105],
            "Low": [99, 100, 101],
            "Close": [102, 103, 104],
            # Volume bilerek eksik
        }
    )

    try:
        calculate_features(data)
    except ValueError as exc:
        assert "Volume" in str(exc)
        return

    raise AssertionError(
        "Eksik OHLCV sütunu kabul edilmemeliydi."
    )
