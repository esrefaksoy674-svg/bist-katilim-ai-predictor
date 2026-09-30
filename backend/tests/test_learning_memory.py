from datetime import date, datetime, timezone

from app.models.learning_event import LearningEvent
from app.services.learning_memory import LearningMemory


def make_event(
    symbol: str,
    signal_date: date,
) -> LearningEvent:
    return LearningEvent(
        symbol=symbol,
        signal_date=signal_date,
        reference_date=date(
            signal_date.year,
            signal_date.month,
            signal_date.day,
        ),
        rise_percent=5.01,
        technical_features={
            "rsi": 55.0,
        },
        news_features={},
        sector_features={},
        created_at=datetime.now(
            timezone.utc
        ),
    )


def test_memory_does_not_duplicate_same_event():
    memory = LearningMemory()

    event = make_event(
        "THYAO",
        date(2026, 9, 28),
    )

    memory.add(event)
    memory.add(event)

    assert memory.count() == 1


def test_memory_keeps_different_events():
    memory = LearningMemory()

    memory.add(
        make_event(
            "THYAO",
            date(2026, 9, 28),
        )
    )

    memory.add(
        make_event(
            "ASELS",
            date(2026, 9, 28),
        )
    )

    assert memory.count() == 2


def test_memory_can_filter_by_symbol():
    memory = LearningMemory()

    memory.add(
        make_event(
            "THYAO",
            date(2026, 9, 28),
        )
    )

    memory.add(
        make_event(
            "ASELS",
            date(2026, 9, 28),
        )
    )

    result = memory.get_by_symbol("THYAO")

    assert len(result) == 1
    assert result[0].symbol == "THYAO"


def test_memory_excludes_future_events():
    memory = LearningMemory()

    memory.add(
        make_event(
            "THYAO",
            date(2026, 9, 20),
        )
    )

    memory.add(
        make_event(
            "ASELS",
            date(2026, 9, 30),
        )
    )

    result = memory.get_before(
        date(2026, 9, 25)
    )

    assert len(result) == 1
    assert result[0].symbol == "THYAO"
