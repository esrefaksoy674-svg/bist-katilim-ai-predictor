from __future__ import annotations

from datetime import date

import pandas as pd

from app.models.learning_event import LearningEvent


def events_to_dataset(
    events: list[LearningEvent],
    feature_names: list[str] | None = None,
    cutoff_date: date | None = None,
) -> tuple[pd.DataFrame, pd.Series]:
    """
    Öğrenme olaylarını zaman-sıralı model eğitim veri setine çevirir.

    Her pozitif öğrenme olayı 1 sınıfıdır. Gelecek sızıntısını önlemek için
    cutoff_date verilirse yalnızca signal_date < cutoff_date kullanılır.

    Negatif sınıflar ayrı piyasa taramasından geldiğinde aynı teknik
    özellik şemasına eklenebilir; bu fonksiyon pozitif olayları hazırlama
    katmanıdır.
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
        row = {
            name: event.technical_features.get(name)
            for name in feature_names
        }
        rows.append(row)
        dates.append(pd.Timestamp(event.signal_date))

    features = pd.DataFrame(rows, index=pd.DatetimeIndex(dates))
    targets = pd.Series(
        [1] * len(rows),
        index=features.index,
        dtype=int,
        name="target",
    )

    return features, targets
