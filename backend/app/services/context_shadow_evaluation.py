from __future__ import annotations

import json

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

from app.services.context_snapshot_repository_factory import get_context_snapshot_repository
from app.services.contextual_dataset import merge_point_in_time_context
from app.services.market_data import fetch_daily_data
from app.services.training_examples import build_labeled_examples
from app.services.universe import fetch_katilim_universe
from app.services.walk_forward import compare_models_walk_forward


METADATA_COLUMNS = {
    "symbol", "reference_date", "target_date", "actual_change_percent", "target"
}
CONTEXT_SOURCES = ("news", "market", "sector")


def _make_model():
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("classifier", RandomForestClassifier(
            n_estimators=50,
            random_state=42,
            class_weight="balanced",
            n_jobs=-1,
        )),
    ])


class _FeatureSubsetModel:
    """Fit one estimator on a named feature view of a shared fold matrix."""

    def __init__(self, factory, columns):
        self.factory = factory
        self.columns = columns

    def fit(self, features, targets):
        self.estimator = self.factory()
        self.estimator.fit(features[self.columns], targets)
        return self

    def predict(self, features):
        return self.estimator.predict(features[self.columns])


def _context_frames(snapshots: list[dict]) -> dict[str, pd.DataFrame]:
    contexts = {}
    for source in CONTEXT_SOURCES:
        rows = []
        for snapshot in snapshots:
            values = snapshot.get(f"{source}_features") or {}
            if not values:
                continue
            rows.append({
                "symbol": snapshot["symbol"],
                "available_date": snapshot["available_date"],
                **values,
            })
        if rows:
            contexts[source] = pd.DataFrame(rows)
    return contexts


def run_context_shadow_evaluation(
    symbols: list[str] | None = None,
    repository=None,
    minimum_context_dates: int = 60,
    minimum_coverage: float = 0.70,
) -> dict:
    """Compare technical-only and context-enriched candidates; never promote.

    Evaluation is withheld until snapshots cover enough distinct sessions
    and enough labeled examples. This prevents early, sparse data from being
    mistaken for model evidence.
    """
    try:
        if repository is None:
            repository = get_context_snapshot_repository()
        snapshots = repository.all()
    except Exception as exc:
        return {"status": "unavailable", "reason": type(exc).__name__}

    snapshot_dates = {
        pd.Timestamp(row["available_date"]).date()
        for row in snapshots
        if row.get("available_date")
    }
    if len(snapshot_dates) < minimum_context_dates:
        return {
            "status": "collecting_context",
            "snapshot_count": len(snapshots),
            "context_date_count": len(snapshot_dates),
            "minimum_context_dates": minimum_context_dates,
        }

    contexts = _context_frames(snapshots)
    if not contexts:
        return {
            "status": "collecting_context",
            "snapshot_count": len(snapshots),
            "reason": "no_numeric_context",
        }

    universe = sorted(set(symbols if symbols is not None else fetch_katilim_universe()))
    frames = []
    errors = 0
    for symbol in universe:
        try:
            examples = build_labeled_examples(
                fetch_daily_data(symbol, period="2y"),
                symbol=symbol,
            )
            if not examples.empty:
                frames.append(examples)
        except Exception:
            errors += 1
    if not frames:
        return {
            "status": "unavailable",
            "reason": "no_market_examples",
            "symbol_errors": errors,
        }

    examples = (
        pd.concat(frames, ignore_index=True)
        .sort_values(["target_date", "symbol"])
        .reset_index(drop=True)
    )
    enriched = merge_point_in_time_context(examples, contexts)
    context_columns = [
        column for column in enriched.columns
        if column.startswith(tuple(f"{source}__" for source in CONTEXT_SOURCES))
    ]
    coverage = (
        float(enriched[context_columns].notna().any(axis=1).mean())
        if context_columns else 0.0
    )
    if coverage < minimum_coverage:
        return {
            "status": "collecting_context",
            "snapshot_count": len(snapshots),
            "context_date_count": len(snapshot_dates),
            "example_count": len(enriched),
            "context_coverage": round(coverage, 4),
            "minimum_coverage": minimum_coverage,
            "symbol_errors": errors,
        }

    baseline_columns = [column for column in examples.columns if column not in METADATA_COLUMNS]
    candidate_columns = [column for column in enriched.columns if column not in METADATA_COLUMNS]
    target_date_index = pd.DatetimeIndex(
        pd.to_datetime(examples["target_date"]), name="target_date"
    )
    baseline_features = examples[baseline_columns].copy()
    baseline_features.index = target_date_index
    candidate_features = enriched[candidate_columns].copy()
    candidate_features.index = target_date_index
    targets = examples["target"].astype(int).copy()
    targets.index = target_date_index

    distinct_dates = len(target_date_index.normalize().unique())
    if distinct_dates < 181:
        return {
            "status": "collecting_context",
            "snapshot_count": len(snapshots),
            "context_date_count": len(snapshot_dates),
            "example_count": len(examples),
            "context_coverage": round(coverage, 4),
            "reason": "not_enough_labeled_sessions",
            "symbol_errors": errors,
        }

    baseline_names = [f"baseline__{column}" for column in baseline_features.columns]
    candidate_names = [f"candidate__{column}" for column in candidate_features.columns]
    shared_windows = pd.concat([
        baseline_features.set_axis(baseline_names, axis=1),
        candidate_features.set_axis(candidate_names, axis=1),
    ], axis=1)
    comparison = compare_models_walk_forward(
        shared_windows,
        targets,
        lambda: _FeatureSubsetModel(_make_model, baseline_names),
        lambda: _FeatureSubsetModel(_make_model, candidate_names),
        initial_train_size=120,
        test_size=20,
        step_size=20,
        gap=1,
    )
    return {
        "status": "evaluated",
        "promoted": False,
        "snapshot_count": len(snapshots),
        "context_date_count": len(snapshot_dates),
        "example_count": len(examples),
        "context_coverage": round(coverage, 4),
        "symbol_errors": errors,
        "comparison": comparison,
    }


if __name__ == "__main__":
    print(json.dumps(run_context_shadow_evaluation(), default=str))
