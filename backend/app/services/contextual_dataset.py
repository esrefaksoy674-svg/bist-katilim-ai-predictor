from __future__ import annotations

from bisect import bisect_left
from datetime import date

import pandas as pd


CONTEXT_KEYS = {"symbol", "available_date"}
OUTCOME_COLUMNS = {"target", "target_date", "actual_change_percent", "rise_percent"}


def merge_point_in_time_context(
    examples: pd.DataFrame,
    contexts: dict[str, pd.DataFrame],
    *,
    symbol_column: str = "symbol",
    reference_date_column: str = "reference_date",
) -> pd.DataFrame:
    """Add latest previously available market/news/sector snapshots to examples.

    Each context frame must contain ``symbol`` and ``available_date`` plus
    numeric feature columns. Context from the example's own reference date is
    deliberately excluded because daily data often lacks publication time;
    this conservative rule prevents same-day news or closing values from
    leaking into a prediction made before they were known. Output columns are
    namespaced by context source (for example ``news__sentiment_score``).
    Missing history stays null so the model's existing imputer can handle it.
    """
    required = {symbol_column, reference_date_column}
    if examples is None or examples.empty:
        return examples.copy() if examples is not None else pd.DataFrame()
    missing = required.difference(examples.columns)
    if missing:
        raise ValueError(f"Training examples are missing columns: {sorted(missing)}")

    result = examples.copy()
    occupied = set(result.columns)
    for source, frame in sorted(contexts.items()):
        if not source or "__" in source:
            raise ValueError("Context source names must be non-empty and cannot contain '__'.")
        if frame is None or frame.empty:
            continue
        missing_context = CONTEXT_KEYS.difference(frame.columns)
        if missing_context:
            raise ValueError(
                f"{source} context is missing columns: {sorted(missing_context)}"
            )
        feature_columns = [
            column for column in frame.columns
            if column not in CONTEXT_KEYS
        ]
        forbidden = OUTCOME_COLUMNS.intersection(feature_columns)
        if forbidden:
            raise ValueError(
                f"Outcome columns cannot be used as context: {sorted(forbidden)}"
            )
        non_numeric = [
            column for column in feature_columns
            if not pd.api.types.is_numeric_dtype(frame[column])
        ]
        if non_numeric:
            raise ValueError(
                f"{source} context features must be numeric: {sorted(non_numeric)}"
            )
        names = {column: f"{source}__{column}" for column in feature_columns}
        collisions = set(names.values()).intersection(occupied)
        if collisions:
            raise ValueError(f"Context feature columns already exist: {sorted(collisions)}")

        indexed: dict[str, tuple[list[date], list[dict]]] = {}
        valid = frame.dropna(subset=["symbol", "available_date"]).copy()
        valid["symbol"] = valid["symbol"].astype(str).str.upper()
        valid["available_date"] = pd.to_datetime(valid["available_date"]).dt.date
        if valid.duplicated(["symbol", "available_date"]).any():
            raise ValueError(
                f"{source} context must have one aggregated row per symbol and date."
            )
        for symbol, group in valid.sort_values("available_date").groupby("symbol"):
            indexed[symbol] = (
                group["available_date"].tolist(),
                group[feature_columns].to_dict("records"),
            )

        additions = []
        for row in result[[symbol_column, reference_date_column]].itertuples(index=False, name=None):
            symbol, reference_date = row
            if pd.isna(symbol) or pd.isna(reference_date):
                additions.append({name: None for name in names.values()})
                continue
            symbol = str(symbol).upper()
            reference_day = pd.Timestamp(reference_date).date()
            dates, records = indexed.get(symbol, ([], []))
            position = bisect_left(dates, reference_day) - 1
            record = records[position] if position >= 0 else {}
            additions.append({
                names[column]: record.get(column)
                for column in feature_columns
            })
        if names:
            result = pd.concat(
                [result, pd.DataFrame(additions, index=result.index)], axis=1
            )
            occupied.update(names.values())
    return result
