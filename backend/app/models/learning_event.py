from datetime import date, datetime

from pydantic import BaseModel, Field


class LearningEvent(BaseModel):
    symbol: str

    signal_date: date
    reference_date: date

    rise_percent: float = Field(gt=5.0)

    technical_features: dict = Field(default_factory=dict)

    news_features: dict = Field(default_factory=dict)

    sector_features: dict = Field(default_factory=dict)

    source_quality: float | None = Field(default=None, ge=0.0, le=1.0)

    created_at: datetime
