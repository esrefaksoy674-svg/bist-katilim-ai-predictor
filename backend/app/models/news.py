from datetime import datetime

from pydantic import BaseModel, Field


class NewsItem(BaseModel):
    title: str
    url: str
    source: str

    published_at: datetime

    symbol: str | None = None
    sector: str | None = None

    news_type: str | None = None
    sentiment: float | None = Field(default=None, ge=-1.0, le=1.0)
    relevance: float | None = Field(default=None, ge=0.0, le=1.0)

    content_hash: str | None = None

    created_at: datetime
