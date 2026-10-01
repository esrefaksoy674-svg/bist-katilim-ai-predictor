from datetime import date, datetime, timezone

import pandas as pd

from app.models.prediction import Prediction
from app.services.prediction_evaluation import evaluate_predictions_for_date


class FakeRepository:
    def __init__(self, prediction):
        self.prediction = prediction

    def get_by_date(self, prediction_date):
        return [self.prediction]

    def add(self, prediction):
        self.prediction = prediction


def test_prediction_evaluation_uses_next_trading_day(monkeypatch):
    prediction = Prediction(
        symbol="TUPRS",
        prediction_date=date(2026, 9, 30),
        target_date=date(2026, 10, 2),
        probability_above_5=0.70,
        expected_change_percent=6.0,
        model_confidence=0.80,
        model_version="v1",
        created_at=datetime.now(timezone.utc),
    )
    repo = FakeRepository(prediction)

    data = pd.DataFrame(
        {
            "Open": [100, 100, 107],
            "High": [101, 101, 108],
            "Low": [99, 99, 106],
            "Close": [100, 100, 107],
            "Volume": [1000, 1000, 1000],
        },
        index=pd.to_datetime(["2026-09-30", "2026-10-01", "2026-10-02"]),
    )

    monkeypatch.setattr(
        "app.services.prediction_evaluation.fetch_daily_data",
        lambda symbol, period="2y": data,
    )

    count = evaluate_predictions_for_date(
        repository=repo,
        prediction_date=date(2026, 9, 30),
        target_date=date(2026, 10, 2),
    )

    assert count == 1
    assert repo.prediction.actual_change_percent == 7.0
    assert repo.prediction.successful is True
