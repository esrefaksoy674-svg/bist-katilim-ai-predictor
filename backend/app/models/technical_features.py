from datetime import date, datetime

from pydantic import BaseModel


class TechnicalFeatures(BaseModel):
    symbol: str
    trading_date: date

    rsi: float | None = None

    macd: float | None = None
    macd_signal: float | None = None
    macd_histogram: float | None = None

    vwap: float | None = None
    atr: float | None = None

    volume: float | None = None
    volume_avg20: float | None = None
    volume_ratio: float | None = None

    sma20: float | None = None
    sma50: float | None = None
    sma200: float | None = None

    momentum: float | None = None
    volatility: float | None = None

    price_vs_vwap_percent: float | None = None
    price_vs_sma20_percent: float | None = None
    price_vs_sma50_percent: float | None = None

    calculated_at: datetime
