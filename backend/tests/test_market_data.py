from datetime import date

import pandas as pd
import pytest

from app.services.market_data import (
    fetch_daily_data,
    get_reference_day,
)


def test_fetch_daily_data_rejects_empty_download(
    monkeypatch,
):
    def fake_download(*args, **kwargs):
        return pd.DataFrame()

    monkeypatch.setattr(
        "app.services.market_data.yf.download",
        fake_download,
    )

    with pytest.raises(RuntimeError):
        fetch_daily_data("THYAO")


def test_fetch_daily_data_normalizes_and_sorts(
    monkeypatch,
):
    index = pd.to_datetime(
        [
            "2026-01-05",
            "2026-01-02",
            "2026-01-06",
        ]
    )

    data = pd.DataFrame(
        {
            "Open": [105, 100, 110],
            "High": [107, 102, 112],
            "Low": [103, 98, 108],
            "Close": [106, 101, 111],
            "Volume": [1000, 900, 1100],
        },
        index=index,
    )

    def fake_download(*args, **kwargs):
        return data

    monkeypatch.setattr(
        "app.services.market_data.yf.download",
        fake_download,
    )

    result = fetch_daily_data("THYAO")

    assert list(result.columns) == [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    ]

    assert result.index.is_monotonic_increasing


def test_get_reference_day_uses_previous_trading_day(
    monkeypatch,
):
    index = pd.to_datetime(
        [
            "2026-01-05",
            "2026-01-06",
            "2026-01-07",
        ]
    )

    data = pd.DataFrame(
        {
            "Open": [100, 110, 120],
            "High": [105, 115, 125],
            "Low": [95, 105, 115],
            "Close": [103, 113, 123],
            "Volume": [1000, 1200, 1400],
        },
        index=index,
    )

    def fake_download(*args, **kwargs):
        return data

    monkeypatch.setattr(
        "app.services.market_data.yf.download",
        fake_download,
    )

    result = get_reference_day(
        "THYAO",
        date(2026, 1, 7),
    )

    assert result["reference_date"] == date(
        2026, 1, 6
    )

    assert result["close"] == 113.0
