from datetime import date, datetime, timezone

from app.models.learning_event import LearningEvent
from app.services.learning_dataset import events_to_dataset


def make_event(symbol, signal_date, rsi):
    return LearningEvent(
        symbol=symbol,
        signal_date=signal_date,
        reference_date=signal_date,
        rise_percent=6.0,
        technical_features={"rsi": rsi, "volume_ratio": 1.5},
        created_at=datetime.now(timezone.utc),
    )


def test_events_to_dataset_is_chronological():
    events = [
        make_event("THYAO", date(2026, 9, 29), 70),
        make_event("ASELS", date(2026, 9, 28), 60),
    ]

    features, targets = events_to_dataset(events)

    assert list(features.index) == [
        features.index[0],
        features.index[1],
    ]
    assert features.index[0].date() == date(2026, 9, 28)
    assert list(targets) == [1, 1]


def test_events_to_dataset_respects_cutoff():
    events = [
        make_event("THYAO", date(2026, 9, 28), 60),
        make_event("ASELS", date(2026, 9, 30), 70),
    ]

    features, targets = events_to_dataset(
        events,
        cutoff_date=date(2026, 9, 30),
    )

    assert len(features) == 1
    assert features.index[0].date() == date(2026, 9, 28)


def test_empty_events_return_empty_dataset():
    features, targets = events_to_dataset([])

    assert features.empty
    assert targets.empty
