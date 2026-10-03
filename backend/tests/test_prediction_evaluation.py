from datetime import date, datetime, timezone

import pytest

import pandas as pd

from app.models.prediction import Prediction
from app.services.prediction_evaluation import (
    evaluate_predictions_for_date,
    evaluate_predictions_for_target_date,
)


class FakeRepository:
    def __init__(self, prediction):
        self.prediction = prediction

    def get_by_date(self, prediction_date):
        return [self.prediction]

    def add(self, prediction):
        self.prediction = prediction


class FakePendingRepository(FakeRepository):
    def get_pending_through_date(self, target_date):
        if self.prediction.target_date <= target_date:
            return [self.prediction]
        return []


def _prediction(target_date):
    return Prediction(
        symbol="TUPRS",
        prediction_date=date(2026, 10, 2),
        target_date=target_date,
        probability_above_5=0.70,
        expected_change_percent=6.0,
        model_confidence=0.80,
        model_version="v1",
        created_at=datetime.now(timezone.utc),
    )


def _market_data():
    return pd.DataFrame(
        {
            "Open": [100, 100, 107],
            "High": [101, 101, 108],
            "Low": [99, 99, 106],
            "Close": [100, 100, 107],
            "Volume": [1000, 1000, 1000],
        },
        index=pd.to_datetime(["2026-09-30", "2026-10-01", "2026-10-02"]),
    )


def test_prediction_evaluation_uses_next_trading_day(monkeypatch):
    prediction = _prediction(date(2026, 10, 2))
    repo = FakeRepository(prediction)
    data = _market_data()

    monkeypatch.setattr(
        "app.services.prediction_evaluation.fetch_daily_data",
        lambda symbol, period="2y": data,
    )

    count = evaluate_predictions_for_date(
        repository=repo,
        prediction_date=date(2026, 10, 2),
        target_date=date(2026, 10, 2),
    )

    assert count == 1
    assert repo.prediction.actual_change_percent == pytest.approx(7.0)
    assert repo.prediction.successful is True


def test_overdue_predictions_are_evaluated_against_their_own_target_date(monkeypatch):
    prediction = _prediction(date(2026, 10, 2))
    repo = FakePendingRepository(prediction)
    data = _market_data()

    monkeypatch.setattr(
        "app.services.prediction_evaluation.fetch_daily_data",
        lambda symbol, period="2y": data,
    )

    count = evaluate_predictions_for_target_date(
        repository=repo,
        target_date=date(2026, 10, 5),
    )

    assert count == 1
    assert repo.prediction.actual_change_percent == pytest.approx(7.0)
    assert repo.prediction.successful is True
