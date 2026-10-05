import pandas as pd
import pytest

from app.services.walk_forward import (
    compare_models_walk_forward,
    evaluate_walk_forward,
)


class LastValueClassifier:
    def fit(self, features, targets):
        self.value = int(targets.iloc[-1])
        return self

    def predict(self, features):
        return [self.value] * len(features)


def test_walk_forward_keeps_same_session_rows_in_one_fold():
    dates = pd.to_datetime([
        "2026-01-01", "2026-01-01", "2026-01-02", "2026-01-02",
        "2026-01-03", "2026-01-03", "2026-01-04", "2026-01-04",
    ])
    features = pd.DataFrame({"value": range(8)}, index=dates)
    targets = pd.Series([0, 1, 0, 1, 1, 1, 0, 0], index=dates)

    result = evaluate_walk_forward(
        features, targets, LastValueClassifier,
        initial_train_size=2, test_size=1, step_size=1,
    )

    assert result.sample_count == 4
    assert len(result.folds) == 2
    assert result.folds[0].train_end < result.folds[0].test_start
    assert result.folds[0].sample_count == 2
    assert result.to_dict()["folds"][0]["test_start"] == "2026-01-03"


def test_walk_forward_gap_and_expanding_windows():
    features = pd.DataFrame({"value": range(12)})
    targets = pd.Series([0, 1] * 6)
    result = evaluate_walk_forward(
        features, targets, LastValueClassifier,
        initial_train_size=4, test_size=2, step_size=2, gap=1,
    )

    assert [(fold.train_end, fold.test_start) for fold in result.folds] == [
        ("3", "5"), ("5", "7"), ("7", "9"), ("9", "11")
    ]
    assert result.sample_count == 7


def test_walk_forward_rejects_unusable_input():
    features = pd.DataFrame({"value": [1, 2]})
    with pytest.raises(ValueError, match="equal lengths"):
        evaluate_walk_forward(features, pd.Series([0]), LastValueClassifier, initial_train_size=1, test_size=1)
    with pytest.raises(ValueError, match="Not enough data"):
        evaluate_walk_forward(features, pd.Series([0, 1]), LastValueClassifier, initial_train_size=2, test_size=1)


def test_model_comparison_uses_identical_fold_dates_and_reports_delta():
    class PositiveClassifier(LastValueClassifier):
        def predict(self, features):
            return [1] * len(features)

    features = pd.DataFrame({"value": range(12)})
    targets = pd.Series([1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1])
    result = compare_models_walk_forward(
        features, targets, LastValueClassifier, PositiveClassifier,
        initial_train_size=4, test_size=2, step_size=2,
    )

    assert [f["test_start"] for f in result["active"]["folds"]] == [
        f["test_start"] for f in result["candidate"]["folds"]
    ]
    assert result["delta"]["recall"] >= 0
    assert result["candidate_is_better"] is True
