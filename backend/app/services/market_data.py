from __future__ import annotations

from datetime import date, datetime, timezone

import pandas as pd
import yfinance as yf


REQUIRED_COLUMNS = [
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
]


def fetch_daily_data(
    symbol: str,
    period: str = "2y",
) -> pd.DataFrame:
    """
    BIST hissesinin günlük OHLCV verisini getirir.

    Canlı işlem veya emir göndermez.
    """

    symbol = symbol.upper().strip()

    if not symbol:
        raise ValueError(
            "Hisse sembolü boş olamaz."
        )

    ticker = f"{symbol}.IS"

    data = yf.download(
        ticker,
        period=period,
        interval="1d",
        auto_adjust=False,
        progress=False,
        threads=False,
    )

    if data is None or data.empty:
        raise RuntimeError(
            f"{symbol} için günlük piyasa verisi alınamadı."
        )

    # Bazı yfinance sürümlerinde MultiIndex gelir.
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [
            column[0]
            for column in data.columns
        ]

    missing = [
        column
        for column in REQUIRED_COLUMNS
        if column not in data.columns
    ]

    if missing:
        raise RuntimeError(
            f"{symbol} verisinde eksik sütunlar: "
            f"{missing}"
        )

    result = data[
        REQUIRED_COLUMNS
    ].copy()

    result = result.dropna(
        subset=[
            "Open",
            "High",
            "Low",
            "Close",
        ]
    )

    if result.empty:
        raise RuntimeError(
            f"{symbol} için kullanılabilir veri kalmadı."
        )

    result.index = pd.to_datetime(
        result.index
    )

    result = result[
        ~result.index.duplicated(
            keep="last"
        )
    ]

    result = result.sort_index()

    if len(result) < 2:
        raise RuntimeError(
            f"{symbol} için yeterli günlük veri yok."
        )

    return result


def get_last_close(
    symbol: str,
) -> dict:
    """
    Son mevcut işlem gününün kapanış verisini döndürür.
    """

    data = fetch_daily_data(
        symbol,
        period="2y",
    )

    row = data.iloc[-1]

    return {
        "symbol": symbol.upper(),
        "trading_date": data.index[-1].date(),
        "open": float(row["Open"]),
        "high": float(row["High"]),
        "low": float(row["Low"]),
        "close": float(row["Close"]),
        "volume": float(row["Volume"]),
        "source": "yfinance",
        "retrieved_at": datetime.now(
            timezone.utc
        ),
    }


def get_reference_day(
    symbol: str,
    signal_date: date,
) -> dict:
    """
    Yükseliş gününden önceki gerçek işlem gününü bulur.

    Takvim günü değil, veri içerisindeki önceki işlem günü
    kullanılır.
    """

    data = fetch_daily_data(
        symbol,
        period="2y",
    )

    eligible = data[
        data.index.date < signal_date
    ]

    if eligible.empty:
        raise RuntimeError(
            f"{symbol} için {signal_date} "
            "öncesinde işlem günü bulunamadı."
        )

    row = eligible.iloc[-1]
    reference_date = eligible.index[-1].date()

    return {
        "symbol": symbol.upper(),
        "signal_date": signal_date,
        "reference_date": reference_date,
        "open": float(row["Open"]),
        "high": float(row["High"]),
        "low": float(row["Low"]),
        "close": float(row["Close"]),
        "volume": float(row["Volume"]),
        "source": "yfinance",
        "retrieved_at": datetime.now(
            timezone.utc
        ),
    }
