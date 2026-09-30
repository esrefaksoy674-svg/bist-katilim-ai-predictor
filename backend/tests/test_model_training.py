import pandas as pd
import pytest

from app.services.model_training import (
    predict_probability,
    train_model,
)


def make_training_data():
    features = pd.DataFrame(
        {
            "rsi": [
                35,
                40,
                45,
                50,
                55,
                60,
                65,
                70,
                42,
                58,
                47,
                63,
            ],
            "volume_ratio": [
                0.8,
                0.9,
                1.0,
                1.1,
                1.3,
                1.5,
                1.7,
                2.0,
                1.0,
                1.4,
                1.1,
                1.6,
            ],
            "momentum": [
                -2,
                -1,
                0,
                1,
                2,
                3,
                4,
                5,
                0.5,
                2.5,
                1.2,
                3.5,
            ],
        }
    )

    targets = pd.Series(
        [
            0,
            0,
            0,
            0,
            1,
            1,
            1,
            1,
            0,
            1,
            0,
            1,
        ]
    )

    return features, targets


def test_model_can_be_trained():
    features, targets = make_training_data()

    trained = train_model(
        features,
        targets,
        validation_ratio=0.25,
    )

    assert trained.sample_count == 9

    assert trained.feature_names == [
        "rsi",
        "volume_ratio",
        "momentum",
    ]

    assert "accuracy" in trained.metrics
    assert "precision" in trained.metrics
    assert "recall" in trained.metrics
    assert "sample_count" in trained.metrics


def test_model_can_predict_probability():
    features, targets = make_training_data()

    trained = train_model(
        features,
        targets,
        validation_ratio=0.25,
    )

    probabilities = predict_probability(
        trained,
        features.iloc[:3],
    )

    assert len(probabilities) == 3

    for probability in probabilities:
        assert 0.0 <= probability <= 1.0


def test_empty_training_data_is_rejected():
    features = pd.DataFrame()
    targets = pd.Series(dtype=int)

    with pytest.raises(ValueError):
        train_model(
            features,
            targets,
        )


def test_single_class_training_data_is_rejected():
    features = pd.DataFrame(
        {
            "rsi": [40, 45, 50, 55, 60, 65, 70, 75, 80, 85],
        }
    )

    targets = pd.Series(
        [1] * 10
    )

    with pytest.raises(ValueError):
        train_model(
            features,
            targets,
        )


def test_missing_prediction_feature_is_rejected():
    features, targets = make_training_data()

    trained = train_model(
        features,
        targets,
        validation_ratio=0.25,
    )

    incomplete = features[
        ["rsi", "momentum"]
    ]

    with pytest.raises(ValueError):
        predict_probability(
            trained,
            incomplete,
        )
