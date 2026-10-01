from app.services.model_promotion import promote_if_better
from app.services.model_registry import ModelRegistry


def test_disabled_learning_blocks_model_promotion():
    from app.services.learning_control import learning_control

    registry = ModelRegistry()
    registry.register_shadow(
        version="v1",
        accuracy=0.80,
        precision=0.80,
        recall=0.80,
        sample_count=100,
    )
    registry.activate("v1")
    registry.register_shadow(
        version="v2",
        accuracy=0.90,
        precision=0.90,
        recall=0.90,
        sample_count=100,
    )

    learning_control.disable()
    try:
        result = promote_if_better(registry, "v2")
    finally:
        learning_control.enable()

    assert result is None
    assert registry.active().version == "v1"


def test_better_shadow_model_is_promoted():
    registry = ModelRegistry()

    registry.register_shadow(
        "0.1.0",
        accuracy=0.60,
        precision=0.60,
        recall=0.60,
        sample_count=100,
    )
    registry.activate("0.1.0")

    registry.register_shadow(
        "0.2.0",
        accuracy=0.70,
        precision=0.65,
        recall=0.62,
        sample_count=120,
    )

    result = promote_if_better(registry, "0.2.0")

    assert result is not None
    assert result.version == "0.2.0"
    assert registry.active().version == "0.2.0"


def test_weaker_shadow_model_stays_shadow():
    registry = ModelRegistry()

    registry.register_shadow(
        "0.1.0",
        accuracy=0.70,
        precision=0.70,
        recall=0.70,
        sample_count=100,
    )
    registry.activate("0.1.0")

    registry.register_shadow(
        "0.2.0",
        accuracy=0.60,
        precision=0.60,
        recall=0.60,
        sample_count=120,
    )

    result = promote_if_better(registry, "0.2.0")

    assert result is None
    assert registry.active().version == "0.1.0"
    assert registry.get("0.2.0").status == "SHADOW"


def test_rollback_restores_archived_model():
    registry = ModelRegistry()

    registry.register_shadow("0.1.0", accuracy=0.60, sample_count=100)
    registry.activate("0.1.0")

    registry.register_shadow("0.2.0", accuracy=0.70, sample_count=100)
    registry.activate("0.2.0")

    result = registry.rollback("0.1.0")

    assert result.version == "0.1.0"
    assert registry.active().version == "0.1.0"
