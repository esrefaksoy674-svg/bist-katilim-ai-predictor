from datetime import date
from types import SimpleNamespace

from app.services.model_persistence import evaluate_daily_predictions


def test_evaluate_daily_predictions_delegates():
    captured = {}

    class FakeRepo:
        pass

    def fake_evaluate(repository, prediction_date, target_date):
        captured["repository"] = repository
        captured["prediction_date"] = prediction_date
        captured["target_date"] = target_date
        return 7

    import app.services.model_persistence as module

    original = module.evaluate_predictions_for_date
    module.evaluate_predictions_for_date = fake_evaluate
    try:
        repo = FakeRepo()
        result = evaluate_daily_predictions(
            prediction_repository=repo,
            prediction_date=date(2026, 9, 30),
            target_date=date(2026, 10, 2),
        )
    finally:
        module.evaluate_predictions_for_date = original

    assert result.evaluated_count == 7
    assert captured["repository"] is repo
    assert captured["prediction_date"] == date(2026, 9, 30)
    assert captured["target_date"] == date(2026, 10, 2)
