from __future__ import annotations

from datetime import date

import pandas as pd

from app.services.market_data import fetch_daily_data
from app.services.training_examples import build_labeled_examples


METADATA_COLUMNS = {
    "symbol",
    "reference_date",
    "target_date",
    "actual_change_percent",
    "target",
}


def build_market_training_dataset(
    symbols: list[str],
    cutoff_date: date | None = None,
    min_history: int = 200,
) -> tuple[pd.DataFrame, pd.Series]:
    """
    Katılım evreninden pozitif ve negatif/baseline örnekleri üretir.

    Özellikler yalnızca referans gününde bilinen veriden hesaplanır.
    cutoff_date verilirse hedef günü cutoff'tan önce olan örnekler tutulur;
    böylece geçmişe dönük doğrulamada gelecek verisi kullanılmaz.
    """
    frames: list[pd.DataFrame] = []
    errors: list[dict] = []

    for symbol in sorted(set(symbols)):
        try:
            data = fetch_daily_data(symbol, period="2y")
            examples = build_labeled_examples(
                data,
                symbol=symbol,
                min_history=min_history,
            )
            if cutoff_date is not None and not examples.empty:
                examples = examples[
                    examples["target_date"] < cutoff_date
                ]
            if not examples.empty:
                frames.append(examples)
        except Exception as exc:
            errors.append({"symbol": symbol, "error": str(exc)})

    if not frames:
        raise ValueError(
            f"Eğitim için kullanılabilir piyasa örneği bulunamadı. "
            f"Hatalı sembol sayısı: {len(errors)}"
        )

    combined = (
        pd.concat(frames, ignore_index=True)
        .sort_values(["target_date", "symbol"])
        .reset_index(drop=True)
    )

    feature_columns = [
        column for column in combined.columns
        if column not in METADATA_COLUMNS
    ]
    # Keep the outcome date as the DatetimeIndex so chronological validation
    # sorts and splits examples by time rather than by the temporary row number.
    features = combined[feature_columns].copy()
    features.index = pd.DatetimeIndex(
        pd.to_datetime(combined["target_date"]),
        name="target_date",
    )
    targets = combined["target"].astype(int).copy()
    targets.index = features.index

    return features, targets
