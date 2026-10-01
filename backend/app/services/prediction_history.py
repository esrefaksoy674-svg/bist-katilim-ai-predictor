from __future__ import annotations

from datetime import date

import pandas as pd

from app.services.market_data import fetch_daily_data
from app.services.training_examples import build_labeled_examples


def build_prediction_history(
    symbols: list[str],
    prediction_date: date,
    min_history: int = 200,
) -> pd.DataFrame:
    """Tahmin benzerlikleri için yalnızca tahmin gününden önceki örnekleri üretir."""
    frames: list[pd.DataFrame] = []

    for symbol in sorted(set(symbols)):
        try:
            data = fetch_daily_data(symbol, period="2y")
            examples = build_labeled_examples(
                data,
                symbol=symbol,
                min_history=min_history,
            )
            if examples.empty:
                continue

            examples = examples[
                pd.to_datetime(examples["reference_date"]).dt.date
                < prediction_date
            ]
            if not examples.empty:
                frames.append(examples)
        except Exception:
            continue

    if not frames:
        return pd.DataFrame()

    return (
        pd.concat(frames, ignore_index=True)
        .sort_values(["reference_date", "symbol"])
        .reset_index(drop=True)
    )
