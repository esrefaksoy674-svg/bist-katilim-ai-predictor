import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator
from ta.volatility import AverageTrueRange


def calculate_features(data: pd.DataFrame) -> dict:
    """
    OHLCV günlük verisinden AI modelinin kullanacağı
    teknik özellikleri hesaplar.
    """

    if data is None or data.empty:
        raise ValueError("Teknik analiz için veri bulunamadı.")

    required = {"Open", "High", "Low", "Close", "Volume"}

    missing = required.difference(data.columns)

    if missing:
        raise ValueError(
            f"Teknik analiz için eksik sütunlar: {sorted(missing)}"
        )

    df = data.copy().sort_index()

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    # RSI
    rsi = RSIIndicator(
        close=close,
        window=14,
    ).rsi()

    # MACD
    macd_indicator = MACD(
        close=close,
        window_fast=12,
        window_slow=26,
        window_sign=9,
    )

    macd = macd_indicator.macd()
    macd_signal = macd_indicator.macd_signal()
    macd_histogram = macd_indicator.macd_diff()

    # ATR
    atr = AverageTrueRange(
        high=high,
        low=low,
        close=close,
        window=14,
    ).average_true_range()

    # Hareketli ortalamalar
    sma20 = SMAIndicator(
        close=close,
        window=20,
    ).sma_indicator()

    sma50 = SMAIndicator(
        close=close,
        window=50,
    ).sma_indicator()

    sma200 = SMAIndicator(
        close=close,
        window=200,
    ).sma_indicator()

    # VWAP
    typical_price = (
        high + low + close
    ) / 3

    cumulative_volume = volume.cumsum()

    vwap = (
        typical_price * volume
    ).cumsum() / cumulative_volume

    # Hacim ortalaması
    volume_avg20 = volume.rolling(20).mean()

    volume_ratio = (
        volume / volume_avg20
    )

    # Momentum
    momentum = close.pct_change(periods=10) * 100

    # Volatilite
    volatility = (
        close.pct_change()
        .rolling(20)
        .std()
        * 100
    )

    last = df.iloc[-1]

    last_close = float(last["Close"])
    last_vwap = _safe_float(vwap.iloc[-1])

    return {
        "rsi": _safe_float(rsi.iloc[-1]),

        "macd": _safe_float(macd.iloc[-1]),
        "macd_signal": _safe_float(
            macd_signal.iloc[-1]
        ),
        "macd_histogram": _safe_float(
            macd_histogram.iloc[-1]
        ),

        "vwap": last_vwap,
        "atr": _safe_float(atr.iloc[-1]),

        "volume": _safe_float(volume.iloc[-1]),
        "volume_avg20": _safe_float(
            volume_avg20.iloc[-1]
        ),
        "volume_ratio": _safe_float(
            volume_ratio.iloc[-1]
        ),

        "sma20": _safe_float(sma20.iloc[-1]),
        "sma50": _safe_float(sma50.iloc[-1]),
        "sma200": _safe_float(sma200.iloc[-1]),

        "momentum": _safe_float(
            momentum.iloc[-1]
        ),
        "volatility": _safe_float(
            volatility.iloc[-1]
        ),

        "price_vs_vwap_percent": _relative_percent(
            last_close,
            last_vwap,
        ),

        "price_vs_sma20_percent": _relative_percent(
            last_close,
            _safe_float(sma20.iloc[-1]),
        ),

        "price_vs_sma50_percent": _relative_percent(
            last_close,
            _safe_float(sma50.iloc[-1]),
        ),
    }


def _safe_float(value):
    if pd.isna(value):
        return None

    return float(value)


def _relative_percent(
    price: float,
    reference: float | None,
) -> float | None:

    if reference is None or reference == 0:
        return None

    return (
        (price - reference)
        / reference
        * 100
    )
