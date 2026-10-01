import pandas as pd
import pytest

from app.services.time_validation import (
    calculate_metrics,
    chronological_split,
)


def test_chronological_split_keeps_time_order():
    features = pd.DataFrame(
        {
            "value": range(10),
        }
    )

    targets = pd.Series(
        [0, 0, 1, 0, 1, 1, 0, 1, 0, 1]
    )

    (
        train_features,
        validation_features,
        train_targets,
        validation_targets,
    ) = chronological_split(
        features,
        targets,
        validation_ratio=0.2,
    )

    assert len(train_features) == 8
    assert len(validation_features) == 2

    assert train_features.iloc[-1]["value"] == 7
    assert validation_features.iloc[0]["value"] == 8

    assert train_targets.iloc[-1] == targets.iloc[7]
    assert validation_targets.iloc[0] == targets.iloc[8]


def test_chronological_split_rejects_short_data():
    features = pd.DataFrame(
        {
            "value": range(5),
        }
    )

    targets = pd.Series(
        [0, 1, 0, 1, 0]
    )

    with pytest.raises(ValueError):
        chronological_split(
            features,
            targets,
        )


def test_chronological_split_allows_same_date_for_multiple_stocks():
    dates = pd.to_datetime([
        "2026-01-02", "2026-01-02", "2026-01-05",
        "2026-01-05", "2026-01-06", "2026-01-07",
        "2026-01-08", "2026-01-09", "2026-01-12", "2026-01-13",
    ])
    features = pd.DataFrame({"value": range(10)}, index=dates)
    targets = pd.Series(range(10), index=dates)

    train_features, validation_features, _, _ = chronological_split(
        features, targets, validation_ratio=0.2
    )

    assert len(train_features) == 8
    assert len(validation_features) == 2
    assert train_features.index.max() <= validation_features.index.min()


def test_metrics_are_calculated():
    actual = [0, 1, 1, 0, 1]
    predicted = [0, 1, 0, 0, 1]

    metrics = calculate_metrics(
        actual,
        predicted,
    )

    assert 0.0 <= metrics["accuracy"] <= 1.0
    assert 0.0 <= metrics["precision"] <= 1.0
    assert 0.0 <= metrics["recall"] <= 1.0
    assert metrics["sample_count"] == 5
