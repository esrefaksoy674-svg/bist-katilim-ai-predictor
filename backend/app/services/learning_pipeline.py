from __future__ import annotations

from datetime import date

from app.services.learning_control import learning_control
from app.services.learning_event import (
    calculate_change_percent,
    create_learning_event,
)
from app.services.learning_memory import learning_memory
from app.services.market_data import get_reference_day
from app.services.technical import calculate_features


def build_learning_event(
    symbol: str,
    signal_date: date,
    signal_close: float,
    technical_data,
    news_features: dict | None = None,
    sector_features: dict | None = None,
):
    """
    >%5 yükseliş olayından öğrenme kaydı oluşturur.

    Teknik özellikler yükseliş gününden değil,
    önceki gerçek işlem gününden alınmalıdır.
    """

    reference = get_reference_day(
        symbol=symbol,
        signal_date=signal_date,
    )

    rise_percent = calculate_change_percent(
        previous_close=reference["close"],
        current_close=signal_close,
    )

    features = calculate_features(
        technical_data
    )

    return create_learning_event(
        symbol=symbol,
        signal_date=signal_date,
        reference_date=reference["reference_date"],
        rise_percent=rise_percent,
        technical_features=features,
        news_features=news_features or {},
        sector_features=sector_features or {},
    )


def process_learning_event(event) -> bool:
    """
    Öğrenme olayını ana belleğe alır.

    Öğrenme kapalıysa mevcut ana bellek değiştirilmez.
    """

    if event is None:
        return False

    if not learning_control.can_learn():
        return False

    learning_memory.add(event)

    return True
