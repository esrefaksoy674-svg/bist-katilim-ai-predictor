import pandas as pd
import pytest

from app.services.model_training import train_model
from app.services.prediction_engine import (
    FEATURE_NAMES,
    build_predictions,
    build_training_matrix,
)


def make_examples():
    dates = pd.date_range("2026-01-02", periods=16, freq="B")
    rows = []
    for i, day in enumerate(dates):
        row = {name: float(i + 1) for name in FEATURE_NAMES}
        row.update(
            {
                "symbol": "THYAO" if i % 2 == 0 else "ASELS",
                "reference_date": day.date(),
                "actual_change_percent": 6.0 if i % 3 else -2.0,
                "target": 1 if i % 3 else 0,
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def test_training_matrix_uses_reference_dates_and_numeric_features():
    examples = make_examples()
    features, targets = build_training_matrix(examples)

    assert list(features.columns) == FEATURE_NAMES
    assert isinstance(features.index, pd.DatetimeIndex)
    assert features.index[0].date() == examples.iloc[0]["reference_date"]
    assert set(targets.unique()) == {0, 1}


def test_prediction_engine_keeps_three_outputs_separate():
    examples = make_examples()
    features, targets = build_training_matrix(examples)
    trained = train_model(features, targets, validation_ratio=0.25)

    candidate = examples.iloc[[-1]].copy()
    candidate["symbol"] = "TUPRS"

    predictions = build_predictions(
        trained_model=trained,
        candidates=candidate,
        history=examples,
        prediction_date=pd.Timestamp("2026-02-01").date(),
        model_version="test-1",
    )

    assert len(predictions) == 1
    result = predictions[0]

    assert 0.0 <= result.probability_above_5 <= 1.0
    assert isinstance(result.expected_change_percent, float)
    assert 0.0 <= result.model_confidence <= 1.0
    assert result.probability_above_5 != result.model_confidence or result.expected_change_percent != result.probability_above_5


def test_prediction_engine_returns_top_n_only():
    examples = make_examples()
    features, targets = build_training_matrix(examples)
    trained = train_model(features, targets, validation_ratio=0.25)

    candidates = examples.iloc[:8].copy()
    candidates["symbol"] = [f"S{i}" for i in range(len(candidates))]

    predictions = build_predictions(
        trained_model=trained,
        candidates=candidates,
        history=examples,
        prediction_date=pd.Timestamp("2026-02-01").date(),
        model_version="test-1",
        top_n=3,
    )

    assert len(predictions) == 3
    assert predictions[0].probability_above_5 >= predictions[1].probability_above_5


def test_prediction_engine_rejects_missing_candidate_feature():
    examples = make_examples()
    features, targets = build_training_matrix(examples)
    trained = train_model(features, targets, validation_ratio=0.25)

    candidate = examples.iloc[[-1]].drop(columns=["rsi"])

    with pytest.raises(ValueError):
        build_predictions(
            trained_model=trained,
            candidates=candidate,
            history=examples,
            prediction_date=pd.Timestamp("2026-02-01").date(),
            model_version="test-1",
        )
