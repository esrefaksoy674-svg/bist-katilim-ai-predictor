from app.services.model_promotion import promote_if_better
from app.services.model_registry import ModelRegistry


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
