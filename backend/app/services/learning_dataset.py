from __future__ import annotations

from datetime import date

import pandas as pd

from app.models.learning_event import LearningEvent

LEARNING_THRESHOLD_PERCENT = 5.0


def events_to_dataset(
    events: list[LearningEvent],
    feature_names: list[str] | None = None,
    cutoff_date: date | None = None,
) -> tuple[pd.DataFrame, pd.Series]:
    """Pozitif öğrenme olaylarını %5 veya üzeri hedef sınıfı olarak hazırlar.

    %5.00 ve üzerindeki gerçek sonuçlar pozitif sınıftır.
    Gerçek değişim yüzdesi ayrıca korunarak sonraki regresyon katmanında
    kullanılabilir.
    """
    filtered = [
        event
        for event in events
        if cutoff_date is None or event.signal_date < cutoff_date
    ]
    if not filtered:
        return pd.DataFrame(), pd.Series(dtype=int)

    filtered.sort(key=lambda event: event.signal_date)

    if feature_names is None:
        names = set()
        for event in filtered:
            names.update(event.technical_features.keys())
        feature_names = sorted(names)

    rows = []
    dates = []
    for event in filtered:
        rows.append({
            name: event.technical_features.get(name)
            for name in feature_names
        })
        dates.append(pd.Timestamp(event.signal_date))

    features = pd.DataFrame(rows, index=pd.DatetimeIndex(dates))
    targets = pd.Series(
        [int(event.rise_percent >= LEARNING_THRESHOLD_PERCENT) for event in filtered],
        index=features.index,
        dtype=int,
        name="target",
    )
    return features, targets


def build_target(change_percent: float) -> int:
    """Sonraki işlem gününün %5 üzeri hedefini üretir."""
    return int(change_percent >= LEARNING_THRESHOLD_PERCENT)


def build_regression_target(change_percent: float) -> float:
    """Gerçek değişim yüzdesini ayrı hedef olarak korur."""
    return float(change_percent)
