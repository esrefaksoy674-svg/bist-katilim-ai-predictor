import pytest

from app.services.model_registry import ModelRegistry


def test_shadow_model_is_registered():
    registry = ModelRegistry()

    model = registry.register_shadow(
        version="0.2.0",
        accuracy=0.62,
        precision=0.60,
        recall=0.58,
        sample_count=100,
        pattern_count=12,
    )

    assert model.version == "0.2.0"
    assert model.status == "SHADOW"
    assert registry.active() is None


def test_shadow_model_can_be_activated():
    registry = ModelRegistry()

    registry.register_shadow(
        version="0.2.0",
        accuracy=0.70,
    )

    model = registry.activate("0.2.0")

    assert model.status == "ACTIVE"
    assert registry.active().version == "0.2.0"


def test_new_shadow_model_does_not_replace_active_model():
    registry = ModelRegistry()

    registry.register_shadow(
        version="0.1.0",
        accuracy=0.60,
    )

    registry.activate("0.1.0")

    registry.register_shadow(
        version="0.2.0",
        accuracy=0.61,
    )

    assert registry.active().version == "0.1.0"


def test_duplicate_model_version_is_rejected():
    registry = ModelRegistry()

    registry.register_shadow(
        version="0.2.0",
    )

    with pytest.raises(ValueError):
        registry.register_shadow(
            version="0.2.0",
        )
