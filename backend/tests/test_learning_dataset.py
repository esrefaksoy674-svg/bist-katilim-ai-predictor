from datetime import date, datetime, timezone

from app.models.learning_event import LearningEvent
from app.services.learning_dataset import build_regression_target, build_target, events_to_dataset


def make_event(symbol, signal_date, rise):
    return LearningEvent(
        symbol=symbol,
        signal_date=signal_date,
        reference_date=signal_date,
        rise_percent=rise,
        technical_features={"rsi": 60},
        created_at=datetime.now(timezone.utc),
    )


def test_threshold_is_strictly_above_five_percent():
    assert build_target(5.00) == 0
    assert build_target(5.01) == 1
    assert build_target(4.99) == 0
    assert build_target(-2.0) == 0


def test_real_change_is_preserved_separately():
    assert build_regression_target(5.00) == 5.00
    assert build_regression_target(12.35) == 12.35
    assert build_regression_target(-3.2) == -3.2


def test_events_to_dataset_is_chronological():
    events = [
        make_event("THYAO", date(2026, 9, 29), 6.0),
        make_event("ASELS", date(2026, 9, 28), 8.0),
    ]
    features, targets = events_to_dataset(events)
    assert features.index[0].date() == date(2026, 9, 28)
    assert list(targets) == [1, 1]


def test_events_to_dataset_respects_cutoff():
    events = [
        make_event("THYAO", date(2026, 9, 28), 6.0),
        make_event("ASELS", date(2026, 9, 30), 8.0),
    ]
    features, targets = events_to_dataset(events, cutoff_date=date(2026, 9, 30))
    assert len(features) == 1


def test_empty_events_return_empty_dataset():
    features, targets = events_to_dataset([])
    assert features.empty
    assert targets.empty
