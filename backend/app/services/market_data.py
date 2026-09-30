from datetime import date, datetime, timezone

import pandas as pd
import yfinance as yf


def fetch_daily_data(symbol: str, period: str = "2y") -> pd.DataFrame:
    """
    Bir BIST hissesinin günlük OHLCV verisini getirir.

    yfinance sembolü BIST için .IS eklenerek oluşturulur.
    """
    ticker = f"{symbol.upper()}.IS"

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

    # yfinance bazı sürümlerde MultiIndex döndürebilir.
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    required = {"Open", "High", "Low", "Close", "Volume"}

    missing = required.difference(data.columns)

    if missing:
        raise RuntimeError(
            f"{symbol} verisinde eksik sütunlar: {sorted(missing)}"
        )

    result = data[list(required)].copy()

    result = result.dropna(
        subset=["Open", "High", "Low", "Close"]
    )

    if result.empty:
        raise RuntimeError(
            f"{symbol} için kullanılabilir günlük veri kalmadı."
        )

    result.index = pd.to_datetime(result.index)

    return result.sort_index()


def get_last_close(symbol: str) -> dict:
    """
    Son mevcut işlem gününün kapanış verisini döndürür.
    Canlı veri kullanılmaz.
    """
    data = fetch_daily_data(symbol, period="2y")

    row = data.iloc[-1]

    trading_date = data.index[-1].date()

    return {
        "symbol": symbol.upper(),
        "trading_date": trading_date,
        "open": float(row["Open"]),
        "high": float(row["High"]),
        "low": float(row["Low"]),
        "close": float(row["Close"]),
        "volume": float(row["Volume"]),
        "source": "yfinance",
        "retrieved_at": datetime.now(timezone.utc),
    }


def get_reference_day(
    symbol: str,
    signal_date: date,
) -> dict:
    """
    Bir yükseliş olayının önceki işlem gününü bulur.

    Örneğin:
        yükseliş günü = 2026-09-28
        referans günü = 2026-09-25

    Hafta sonu/tatil nedeniyle takvim günü değil,
    gerçek önceki işlem günü kullanılır.
    """
    data = fetch_daily_data(symbol, period="2y")

    dates = [index.date() for index in data.index]

    previous_dates = [
        item for item in dates
        if item < signal_date
    ]

    if not previous_dates:
        raise RuntimeError(
            f"{symbol} için {signal_date} öncesinde işlem günü bulunamadı."
        )

    reference_date = previous_dates[-1]
    row = data.loc[
        data.index.date == reference_date
    ].iloc[-1]

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
        "retrieved_at": datetime.now(timezone.utc),
    }
