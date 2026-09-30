from app.services.model_evaluation import (
    ModelMetrics,
    evaluate_candidate,
    is_better_model,
)


def test_better_candidate_is_detected():
    active = ModelMetrics(
        accuracy=0.60,
        precision=0.58,
        recall=0.55,
        sample_count=100,
    )

    candidate = ModelMetrics(
        accuracy=0.62,
        precision=0.59,
        recall=0.56,
        sample_count=100,
    )

    assert is_better_model(
        candidate,
        active,
    ) is True


def test_worse_candidate_is_not_better():
    active = ModelMetrics(
        accuracy=0.60,
        precision=0.58,
        recall=0.55,
        sample_count=100,
    )

    candidate = ModelMetrics(
        accuracy=0.59,
        precision=0.60,
        recall=0.57,
        sample_count=100,
    )

    assert is_better_model(
        candidate,
        active,
    ) is False


def test_equal_candidate_does_not_replace_active():
    active = ModelMetrics(
        accuracy=0.60,
        precision=0.58,
        recall=0.55,
        sample_count=100,
    )

    candidate = ModelMetrics(
        accuracy=0.60,
        precision=0.58,
        recall=0.55,
        sample_count=100,
    )

    assert is_better_model(
        candidate,
        active,
    ) is False


def test_candidate_without_samples_is_rejected():
    candidate = ModelMetrics(
        accuracy=0.90,
        precision=0.90,
        recall=0.90,
        sample_count=0,
    )

    assert evaluate_candidate(
        candidate,
        None,
    ) == "REJECTED"


def test_candidate_without_active_model_is_eligible():
    candidate = ModelMetrics(
        accuracy=0.60,
        precision=0.58,
        recall=0.55,
        sample_count=100,
    )

    assert evaluate_candidate(
        candidate,
        None,
    ) == "ELIGIBLE"


def test_worse_candidate_remains_shadow():
    active = ModelMetrics(
        accuracy=0.70,
        precision=0.65,
        recall=0.60,
        sample_count=200,
    )

    candidate = ModelMetrics(
        accuracy=0.69,
        precision=0.66,
        recall=0.61,
        sample_count=200,
    )

    assert evaluate_candidate(
        candidate,
        active,
    ) == "SHADOW"
