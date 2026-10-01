from __future__ import annotations

from datetime import date

import pandas as pd

from app.services.learning_dataset import build_target
from app.services.technical import calculate_features


def build_labeled_examples(
    data: pd.DataFrame,
    symbol: str,
    min_history: int = 200,
) -> pd.DataFrame:
    """
    Günlük OHLCV verisinden zaman sızıntısı olmayan eğitim örnekleri üretir.

    Her satırın özellikleri referans işlem gününün kapanışında bilinen veriden,
    etiketi ise yalnızca bir sonraki işlem gününün kapanış değişiminden oluşur.
    """
    required = {"Open", "High", "Low", "Close", "Volume"}
    if data is None or data.empty:
        raise ValueError("Eğitim için piyasa verisi boş.")
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"Eğitim verisinde eksik sütunlar: {sorted(missing)}")

    working = data[list(required)].copy().sort_index()
    working = working[~working.index.duplicated(keep="last")]

    if len(working) <= min_history:
        return pd.DataFrame()

    rows = []
    for index in range(min_history, len(working) - 1):
        reference = working.iloc[index]
        next_day = working.iloc[index + 1]
        history = working.iloc[: index + 1]

        features = calculate_features(history)
        previous_close = float(reference["Close"])
        next_close = float(next_day["Close"])

        if previous_close <= 0:
            continue

        change_percent = (next_close - previous_close) / previous_close * 100

        row = dict(features)
        row.update(
            {
                "symbol": symbol.upper(),
                "reference_date": working.index[index].date(),
                "target_date": working.index[index + 1].date(),
                "actual_change_percent": change_percent,
                "target": build_target(change_percent),
            }
        )
        rows.append(row)

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows).sort_values("reference_date").reset_index(drop=True)
