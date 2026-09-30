from datetime import date, datetime

from pydantic import BaseModel, Field


class Stock(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    name: str | None = None
    is_katilim: bool = True
    active: bool = True
    valid_from: date | None = None
    valid_to: date | None = None
    updated_at: datetime | None = None
