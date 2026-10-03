from datetime import date, datetime, timezone

from app.models.prediction import Prediction
from app.services.prediction_repository import SupabasePredictionRepository


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows

    def upsert(self, row, on_conflict=None):
        return self

    def select(self, value):
        return self

    def eq(self, key, value):
        return self

    def order(self, value, desc=False):
        return self

    def limit(self, count):
        return self

    def execute(self):
        return FakeResponse(self.rows)


class FakeClient:
    def __init__(self, rows=None):
        self.rows = rows or []

    def table(self, name):
        return FakeQuery(self.rows)


def test_prediction_repository_round_trip():
    prediction = Prediction(
        symbol="TUPRS",
        prediction_date=date(2026, 10, 1),
        target_date=date(2026, 10, 2),
        probability_above_5=0.62,
        expected_change_percent=6.4,
        model_confidence=0.71,
        pattern_count=12,
        explanation={"method": "statistical"},
        model_version="v1",
        created_at=datetime.now(timezone.utc),
    )

    row = SupabasePredictionRepository._to_row(prediction)
    restored = SupabasePredictionRepository._from_row(row)

    assert restored.symbol == "TUPRS"
    assert restored.probability_above_5 == 0.62
    assert restored.pattern_count == 12


def test_prediction_repository_get_by_date():
    prediction = Prediction(
        symbol="TUPRS",
        prediction_date=date(2026, 10, 1),
        target_date=date(2026, 10, 2),
        probability_above_5=0.62,
        expected_change_percent=6.4,
        model_confidence=0.71,
        model_version="v1",
        created_at=datetime.now(timezone.utc),
    )
    row = SupabasePredictionRepository._to_row(prediction)
    repo = SupabasePredictionRepository(FakeClient([row]))

    results = repo.get_by_date(date(2026, 10, 1))

    assert len(results) == 1
    assert results[0].symbol == "TUPRS"



def test_prediction_repository_returns_latest_prediction_date():
    repo = SupabasePredictionRepository(
        FakeClient([{"prediction_date": "2026-10-02"}])
    )

    assert repo.get_latest_date() == date(2026, 10, 2)


def test_prediction_repository_returns_none_when_no_predictions_exist():
    repo = SupabasePredictionRepository(FakeClient())

    assert repo.get_latest_date() is None
