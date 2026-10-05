from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Callable

import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score


@dataclass(frozen=True)
class WalkForwardFold:
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    sample_count: int
    accuracy: float
    precision: float
    recall: float


@dataclass(frozen=True)
class WalkForwardResult:
    sample_count: int
    accuracy: float
    precision: float
    recall: float
    folds: tuple[WalkForwardFold, ...]

    def to_dict(self) -> dict:
        result = asdict(self)
        result["folds"] = [asdict(fold) for fold in self.folds]
        return result


def evaluate_walk_forward(
    features: pd.DataFrame,
    targets: pd.Series,
    model_factory: Callable[[], object],
    *,
    initial_train_size: int,
    test_size: int,
    step_size: int | None = None,
    gap: int = 0,
) -> WalkForwardResult:
    """Evaluate a model on expanding, chronological windows.

    Datetime-indexed examples are split by distinct dates so examples for one
    trading session can never land in both train and test. ``gap`` and window
    sizes are measured in dates for datetime indexes and rows otherwise.
    Each fold gets a fresh estimator. The same function can therefore compare
    an active model and a challenger on identical windows.
    """
    if len(features) != len(targets):
        raise ValueError("Features and targets must have equal lengths.")
    if initial_train_size < 1 or test_size < 1 or gap < 0:
        raise ValueError("Window sizes must be positive and gap non-negative.")
    step = test_size if step_size is None else step_size
    if step < 1:
        raise ValueError("step_size must be positive.")
    if features.empty:
        raise ValueError("Walk-forward evaluation requires data.")

    ordered_x, ordered_y = features.copy(), targets.copy()
    by_date = isinstance(ordered_x.index, pd.DatetimeIndex)
    if by_date:
        order = ordered_x.index.argsort(kind="stable")
        ordered_x = ordered_x.iloc[order]
        ordered_y = ordered_y.iloc[order]
        keys = pd.Index(ordered_x.index.normalize().unique()).sort_values()
    else:
        keys = pd.RangeIndex(len(ordered_x))

    actual_all: list[int] = []
    predicted_all: list[int] = []
    folds: list[WalkForwardFold] = []
    train_end = initial_train_size

    while train_end + gap < len(keys):
        test_start = train_end + gap
        test_end = min(test_start + test_size, len(keys))
        if test_start >= test_end:
            break
        if by_date:
            train_dates = keys[:train_end]
            test_dates = keys[test_start:test_end]
            train_mask = ordered_x.index.normalize().isin(train_dates)
            test_mask = ordered_x.index.normalize().isin(test_dates)
            x_train, y_train = ordered_x.loc[train_mask], ordered_y.loc[train_mask]
            x_test, y_test = ordered_x.loc[test_mask], ordered_y.loc[test_mask]
            train_start_label, train_end_label = str(train_dates[0].date()), str(train_dates[-1].date())
            test_start_label, test_end_label = str(test_dates[0].date()), str(test_dates[-1].date())
        else:
            x_train, y_train = ordered_x.iloc[:train_end], ordered_y.iloc[:train_end]
            x_test, y_test = ordered_x.iloc[test_start:test_end], ordered_y.iloc[test_start:test_end]
            train_start_label, train_end_label = "0", str(train_end - 1)
            test_start_label, test_end_label = str(test_start), str(test_end - 1)

        estimator = model_factory()
        estimator.fit(x_train, y_train)
        predicted = estimator.predict(x_test)
        actual = y_test.astype(int).tolist()
        predicted_values = [int(value) for value in predicted]
        actual_all.extend(actual)
        predicted_all.extend(predicted_values)
        folds.append(
            WalkForwardFold(
                train_start=train_start_label,
                train_end=train_end_label,
                test_start=test_start_label,
                test_end=test_end_label,
                sample_count=len(actual),
                accuracy=float(accuracy_score(actual, predicted_values)),
                precision=float(precision_score(actual, predicted_values, zero_division=0)),
                recall=float(recall_score(actual, predicted_values, zero_division=0)),
            )
        )
        if test_end == len(keys):
            break
        train_end += step

    if not actual_all:
        raise ValueError("Not enough data to produce a walk-forward test fold.")
    return WalkForwardResult(
        sample_count=len(actual_all),
        accuracy=float(accuracy_score(actual_all, predicted_all)),
        precision=float(precision_score(actual_all, predicted_all, zero_division=0)),
        recall=float(recall_score(actual_all, predicted_all, zero_division=0)),
        folds=tuple(folds),
    )


def compare_models_walk_forward(
    features: pd.DataFrame,
    targets: pd.Series,
    active_model_factory: Callable[[], object],
    candidate_model_factory: Callable[[], object],
    *,
    initial_train_size: int,
    test_size: int,
    step_size: int | None = None,
    gap: int = 0,
) -> dict:
    """Compare active and candidate estimators over the same time windows.

    The candidate is marked better only when the aggregate metric tuple
    (accuracy, precision, recall) improves lexicographically. Existing
    production promotion remains opt-in and is not changed by this report.
    """
    common = {
        "initial_train_size": initial_train_size,
        "test_size": test_size,
        "step_size": step_size,
        "gap": gap,
    }
    active = evaluate_walk_forward(
        features, targets, active_model_factory, **common
    )
    candidate = evaluate_walk_forward(
        features, targets, candidate_model_factory, **common
    )
    active_score = (active.accuracy, active.precision, active.recall)
    candidate_score = (candidate.accuracy, candidate.precision, candidate.recall)
    return {
        "active": active.to_dict(),
        "candidate": candidate.to_dict(),
        "delta": {
            "accuracy": candidate.accuracy - active.accuracy,
            "precision": candidate.precision - active.precision,
            "recall": candidate.recall - active.recall,
        },
        "candidate_is_better": candidate_score > active_score,
    }
