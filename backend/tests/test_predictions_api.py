from datetime import date
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import app


class FakePredictionRepository:
    def get_by_date(self, prediction_date):
        assert prediction_date == date(2026, 9, 28)
        return []


def test_predictions_api_reads_requested_date(monkeypatch):
    monkeypatch.setattr(
        "app.main.get_prediction_repository",
        lambda: FakePredictionRepository(),
    )

    client = TestClient(app)
    response = client.get("/predictions?prediction_date=2026-09-28")

    assert response.status_code == 200
    assert response.json() == {
        "prediction_date": "2026-09-28",
        "count": 0,
        "predictions": [],
    }


def test_predictions_api_defaults_to_latest_available_date(monkeypatch):
    class LatestRepository:
        def get_latest_date(self):
            return date(2026, 10, 2)

        def get_by_date(self, prediction_date):
            assert prediction_date == date(2026, 10, 2)
            return []

    monkeypatch.setattr(
        "app.main.get_prediction_repository",
        lambda: LatestRepository(),
    )

    client = TestClient(app)
    response = client.get("/predictions")

    assert response.status_code == 200
    assert response.json()["prediction_date"] == "2026-10-02"
    assert response.json()["predictions"] == []


def test_predictions_api_shows_only_next_session_rows_with_five_percent_expected_gain(monkeypatch):
    class MixedRepository:
        def get_by_date(self, prediction_date):
            assert prediction_date == date(2026, 10, 2)
            return [
                SimpleNamespace(
                    symbol="EDGE",
                    target_date=date(2026, 10, 5),
                    probability_above_5=0.20,
                    expected_change_percent=5.0,
                    model_confidence=0.936,
                    pattern_count=10,
                    explanation={},
                    model_version="v2",
                    actual_change_percent=None,
                    successful=None,
                    evaluated_at=None,
                ),
                SimpleNamespace(
                    symbol="HIGH",
                    target_date=date(2026, 10, 5),
                    probability_above_5=0.90,
                    expected_change_percent=6.1,
                    model_confidence=0.936,
                    pattern_count=9,
                    explanation={},
                    model_version="v2",
                    actual_change_percent=None,
                    successful=None,
                    evaluated_at=None,
                ),
                SimpleNamespace(
                    symbol="STALE",
                    target_date=date(2026, 10, 2),
                    probability_above_5=0.8,
                    expected_change_percent=9.0,
                    model_confidence=0.9,
                    pattern_count=4,
                    explanation={},
                    model_version="v1",
                    actual_change_percent=None,
                    successful=None,
                    evaluated_at=None,
                ),
                SimpleNamespace(
                    symbol="LOW",
                    target_date=date(2026, 10, 5),
                    probability_above_5=0.99,
                    expected_change_percent=4.99,
                    model_confidence=0.9,
                    pattern_count=4,
                    explanation={},
                    model_version="v1",
                    actual_change_percent=None,
                    successful=None,
                    evaluated_at=None,
                ),
            ]

    monkeypatch.setattr(
        "app.main.get_prediction_repository",
        lambda: MixedRepository(),
    )

    client = TestClient(app)
    response = client.get("/predictions?prediction_date=2026-10-02")

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 2
    assert [row["symbol"] for row in payload["predictions"]] == ["EDGE", "HIGH"]
    assert {row["target_date"] for row in payload["predictions"]} == {"2026-10-05"}


def test_predictions_api_returns_503_when_repository_fails(monkeypatch):
    def fail():
        raise RuntimeError("Supabase unavailable")

    monkeypatch.setattr("app.main.get_prediction_repository", fail)

    client = TestClient(app)
    response = client.get("/predictions?prediction_date=2026-09-28")

    assert response.status_code == 503
    assert "Tahmin kayıtları alınamadı" in response.json()["detail"]
