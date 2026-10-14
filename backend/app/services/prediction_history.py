from __future__ import annotations

from datetime import date

import pandas as pd

from app.services.market_data import fetch_daily_data
from app.services.training_examples import build_labeled_examples


def build_prediction_history(
    symbols: list[str],
    prediction_date: date,
    min_history: int = 200,
    scan_status: dict | None = None,
) -> pd.DataFrame:
    """Build prior examples and report per-symbol failures instead of hiding them."""
    unique_symbols = sorted(set(symbols))
    frames: list[pd.DataFrame] = []
    status = {
        "universe_count": len(unique_symbols),
        "attempted_count": 0,
        "data_received_count": 0,
        "symbols_with_examples": 0,
        "empty_examples_count": 0,
        "error_count": 0,
        "failed_symbols": [],
        "coverage_verified": False,
    }

    for symbol in unique_symbols:
        status["attempted_count"] += 1
        try:
            data = fetch_daily_data(symbol, period="2y")
            status["data_received_count"] += 1
            examples = build_labeled_examples(
                data,
                symbol=symbol,
                min_history=min_history,
            )
            if examples.empty:
                status["empty_examples_count"] += 1
                continue

            examples = examples[
                pd.to_datetime(examples["reference_date"]).dt.date
                < prediction_date
            ]
            if not examples.empty:
                frames.append(examples)
                status["symbols_with_examples"] += 1
            else:
                status["empty_examples_count"] += 1
        except Exception as exc:
            status["error_count"] += 1
            status["failed_symbols"].append({
                "symbol": symbol,
                "error": type(exc).__name__,
            })

    status["coverage_verified"] = (
        status["attempted_count"] == status["universe_count"]
        and status["error_count"] == 0
    )
    status["status"] = (
        "COMPLETE" if status["coverage_verified"] else "INCOMPLETE"
    )
    if scan_status is not None:
        scan_status.update(status)

    if not frames:
        return pd.DataFrame()

    return (
        pd.concat(frames, ignore_index=True)
        .sort_values(["reference_date", "symbol"])
        .reset_index(drop=True)
    )
