import pandas as pd
import pytest

from app.models.learning_event import LearningEvent
from app.services.model_registry import ModelRegistry
from app.services.persistent_training import train_from_learning_memory


class FakeRepository:
    def __init__(self, events):
        self.events = events

    def all(self):
        return self.events


def make_event(symbol, signal_date, rise):
    return LearningEvent(
        symbol=symbol,
        signal_date=signal_date,
        reference_date=signal_date,
        rise_percent=rise,
        technical_features={"rsi": 60.0, "volume_ratio": 1.2},
        created_at=pd.Timestamp(
            "2026-09-28",
            tz="UTC",
        ).to_pydatetime(),
    )


def test_persistent_training_rejects_empty_memory():
    with pytest.raises(ValueError, match="kalıcı öğrenme verisi"):
        train_from_learning_memory(
            version="empty",
            registry=ModelRegistry(),
            repository=FakeRepository([]),
        )


def test_persistent_training_requires_two_target_classes():
    events = [
        make_event("THYAO", pd.Timestamp("2026-09-20").date(), 6.0),
        make_event("ASELS", pd.Timestamp("2026-09-21").date(), 8.0),
    ]

    with pytest.raises(ValueError, match="iki hedef sınıf"):
        train_from_learning_memory(
            version="positive-only",
            registry=ModelRegistry(),
            repository=FakeRepository(events),
        )


def test_persistent_training_delegates_to_training_pipeline(monkeypatch):
    events = [
        make_event("AAA", pd.Timestamp("2026-09-20").date(), 6.0),
        make_event("BBB", pd.Timestamp("2026-09-21").date(), 7.0),
    ]

    features = pd.DataFrame(
        {"rsi": [55.0, 45.0]},
        index=pd.to_datetime(["2026-09-20", "2026-09-21"]),
    )
    targets = pd.Series(
        [0, 1],
        index=features.index,
        dtype=int,
    )

    monkeypatch.setattr(
        "app.services.persistent_training.events_to_dataset",
        lambda events: (features, targets),
    )

    sentinel = object()

    monkeypatch.setattr(
        "app.services.persistent_training.train_shadow_model",
        lambda **kwargs: sentinel,
    )

    result = train_from_learning_memory(
        version="delegated",
        registry=ModelRegistry(),
        repository=FakeRepository(events),
    )

    assert result is sentinel
