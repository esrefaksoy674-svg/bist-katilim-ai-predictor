from datetime import date, datetime

from pydantic import BaseModel, Field


class Prediction(BaseModel):
    symbol: str

    prediction_date: date
    target_date: date

    probability_above_5: float = Field(ge=0.0, le=1.0)
    expected_change_percent: float

    model_confidence: float = Field(ge=0.0, le=1.0)

    pattern_count: int = Field(default=0, ge=0)

    explanation: dict = Field(default_factory=dict)

    model_version: str

    actual_change_percent: float | None = None
    successful: bool | None = None

    evaluated_at: datetime | None = None
    created_at: datetime
