import pandas as pd
import pytest

from app.services.learning_control import learning_control
from app.services.model_registry import ModelRegistry
from app.services.training_pipeline import train_shadow_model


def make_data():
    dates = pd.date_range("2026-01-02", periods=12, freq="B")
    features = pd.DataFrame(
        {
            "rsi": [35, 40, 45, 50, 55, 60, 65, 70, 42, 58, 47, 63],
            "volume_ratio": [0.8, 0.9, 1.0, 1.1, 1.3, 1.5, 1.7, 2.0, 1.0, 1.4, 1.1, 1.6],
            "momentum": [-2, -1, 0, 1, 2, 3, 4, 5, 0.5, 2.5, 1.2, 3.5],
        },
        index=dates,
    )
    targets = pd.Series([0, 0, 0, 0, 1, 1, 1, 1, 0, 1, 0, 1], index=dates)
    return features, targets


@pytest.fixture(autouse=True)
def reset_learning():
    learning_control.enable()
    yield
    learning_control.enable()


def test_training_registers_shadow_model_without_forced_activation():
    features, targets = make_data()
    registry = ModelRegistry()

    result = train_shadow_model(
        features,
        targets,
        version="test-shadow",
        registry=registry,
        promote=False,
    )

    assert result.registered_model.status == "SHADOW"
    assert registry.active() is None
    assert result.active_model is None
    assert result.registered_model.artifact is result.trained_model


def test_learning_disabled_blocks_promotion_but_allows_shadow_training():
    learning_control.disable()
    features, targets = make_data()
    registry = ModelRegistry()

    result = train_shadow_model(
        features,
        targets,
        version="test-disabled",
        registry=registry,
        promote=True,
    )

    assert result.registered_model.status == "SHADOW"
    assert result.promoted_model is None
    assert result.active_model is None
    assert registry.active() is None
