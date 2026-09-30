from datetime import date, datetime

from pydantic import BaseModel, Field


class MarketData(BaseModel):
    symbol: str
    trading_date: date

    open: float = Field(ge=0)
    high: float = Field(ge=0)
    low: float = Field(ge=0)
    close: float = Field(ge=0)

    volume: float = Field(ge=0)

    change_percent: float | None = None

    source: str
    retrieved_at: datetime
