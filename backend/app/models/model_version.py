from datetime import datetime

from pydantic import BaseModel, Field


class ModelVersion(BaseModel):
    version: str

    status: str

    accuracy: float | None = Field(default=None, ge=0.0, le=1.0)
    precision: float | None = Field(default=None, ge=0.0, le=1.0)
    recall: float | None = Field(default=None, ge=0.0, le=1.0)

    sample_count: int = Field(default=0, ge=0)
    pattern_count: int = Field(default=0, ge=0)

    training_start: datetime | None = None
    training_end: datetime | None = None

    created_at: datetime
    activated_at: datetime | None = None
