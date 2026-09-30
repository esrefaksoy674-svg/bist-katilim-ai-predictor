from datetime import date, datetime, timezone

from app.models.learning_event import LearningEvent
from app.services.learning_control import LearningControl
from app.services.learning_memory import LearningMemory
from app.services.learning_pipeline import process_learning_event


def make_event() -> LearningEvent:
    return LearningEvent(
        symbol="THYAO",
        signal_date=date(2026, 9, 28),
        reference_date=date(2026, 9, 25),
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


def test_learning_control_can_enable_and_disable():
    control = LearningControl()

    assert control.is_enabled() is True

    control.disable()

    assert control.is_enabled() is False
    assert control.can_learn() is False

    control.enable()

    assert control.is_enabled() is True
    assert control.can_learn() is True


def test_disabled_learning_does_not_change_memory(
    monkeypatch,
):
    control = LearningControl()
    memory = LearningMemory()

    control.disable()

    monkeypatch.setattr(
        "app.services.learning_pipeline.learning_control",
        control,
    )

    monkeypatch.setattr(
        "app.services.learning_pipeline.learning_memory",
        memory,
    )

    result = process_learning_event(
        make_event()
    )

    assert result is False
    assert memory.count() == 0


def test_enabled_learning_adds_to_memory(
    monkeypatch,
):
    control = LearningControl()
    memory = LearningMemory()

    control.enable()

    monkeypatch.setattr(
        "app.services.learning_pipeline.learning_control",
        control,
    )

    monkeypatch.setattr(
        "app.services.learning_pipeline.learning_memory",
        memory,
    )

    result = process_learning_event(
        make_event()
    )

    assert result is True
    assert memory.count() == 1
