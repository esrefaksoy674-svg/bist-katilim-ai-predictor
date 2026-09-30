from __future__ import annotations

from datetime import date, datetime, timezone

from app.models.learning_event import LearningEvent


LEARNING_THRESHOLD_PERCENT = 5.0


def calculate_change_percent(
    previous_close: float,
    current_close: float,
) -> float:
    if previous_close <= 0:
        raise ValueError(
            "Önceki kapanış sıfırdan büyük olmalıdır."
        )

    return (
        (current_close - previous_close)
        / previous_close
        * 100
    )


def is_learning_event(
    rise_percent: float,
) -> bool:
    """
    Yalnızca %5'in ÜZERİNDEKİ yükselişler öğrenmeye girer.

    %5.00 -> False
    %5.01 -> True
    """

    return rise_percent > LEARNING_THRESHOLD_PERCENT


def create_learning_event(
    symbol: str,
    signal_date: date,
    reference_date: date,
    rise_percent: float,
    technical_features: dict | None = None,
    news_features: dict | None = None,
    sector_features: dict | None = None,
    source_quality: float | None = None,
) -> LearningEvent | None:

    if not is_learning_event(rise_percent):
        return None

    return LearningEvent(
        symbol=symbol.upper(),
        signal_date=signal_date,
        reference_date=reference_date,
        rise_percent=rise_percent,
        technical_features=technical_features or {},
        news_features=news_features or {},
        sector_features=sector_features or {},
        source_quality=source_quality,
        created_at=datetime.now(timezone.utc),
    )
