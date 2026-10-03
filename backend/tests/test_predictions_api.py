from datetime import date

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


def test_predictions_api_returns_503_when_repository_fails(monkeypatch):
    def fail():
        raise RuntimeError("Supabase unavailable")

    monkeypatch.setattr("app.main.get_prediction_repository", fail)

    client = TestClient(app)
    response = client.get("/predictions?prediction_date=2026-09-28")

    assert response.status_code == 503
    assert "Tahmin kayıtları alınamadı" in response.json()["detail"]
