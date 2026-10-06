from datetime import date
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import app


def test_predictions_api_uses_latest_completed_session_and_filters_negative(monkeypatch):
    class Repo:
        def get_by_date(self, prediction_date):
            assert prediction_date == date(2026, 10, 6)
            return [
                SimpleNamespace(
                    symbol="NEG",
                    target_date=date(2026, 10, 7),
                    probability_above_5=0.99,
                    expected_change_percent=-2.0,
                    model_confidence=1.0,
                    pattern_count=10,
                    explanation={},
                    model_version="v1",
                    actual_change_percent=None,
                    successful=None,
                    evaluated_at=None,
                ),
                SimpleNamespace(
                    symbol="POS",
                    target_date=date(2026, 10, 7),
                    probability_above_5=0.90,
                    expected_change_percent=6.0,
                    model_confidence=1.0,
                    pattern_count=10,
                    explanation={},
                    model_version="v2",
                    actual_change_percent=None,
                    successful=None,
                    evaluated_at=None,
                ),
                SimpleNamespace(
                    symbol="STALE_TARGET",
                    target_date=date(2026, 10, 6),
                    probability_above_5=1.0,
                    expected_change_percent=10.0,
                    model_confidence=1.0,
                    pattern_count=10,
                    explanation={},
                    model_version="v1",
                    actual_change_percent=None,
                    successful=None,
                    evaluated_at=None,
                ),
            ]

    monkeypatch.setattr("app.main.get_prediction_repository", lambda: Repo())
    monkeypatch.setattr("app.main.latest_trading_day", lambda _: date(2026, 10, 6))
    monkeypatch.setattr("app.main.next_trading_day", lambda _: date(2026, 10, 7))

    response = TestClient(app).get("/predictions?prediction_date=2026-10-05")

    assert response.status_code == 200
    payload = response.json()
    assert payload["prediction_date"] == "2026-10-06"
    assert [row["symbol"] for row in payload["predictions"]] == ["POS"]


def test_predictions_api_does_not_fall_back_to_oldest_saved_date(monkeypatch):
    class Repo:
        def get_by_date(self, prediction_date):
            assert prediction_date == date(2026, 10, 6)
            return []

    monkeypatch.setattr("app.main.get_prediction_repository", lambda: Repo())
    monkeypatch.setattr("app.main.latest_trading_day", lambda _: date(2026, 10, 6))
    monkeypatch.setattr("app.main.next_trading_day", lambda _: date(2026, 10, 7))

    response = TestClient(app).get("/predictions")

    assert response.status_code == 200
    assert response.json()["prediction_date"] == "2026-10-06"
    assert response.json()["predictions"] == []


def test_learning_control_can_be_read_and_changed():
    client = TestClient(app)
    client.post("/learning-control?enabled=false")
    response = client.get("/learning-control")
    assert response.status_code == 200
    assert response.json()["enabled"] is False

    client.post("/learning-control?enabled=true")
    response = client.get("/learning-control")
    assert response.json()["enabled"] is True


def test_predictions_api_returns_503_when_repository_fails(monkeypatch):
    def fail():
        raise RuntimeError("Supabase unavailable")

    monkeypatch.setattr("app.main.get_prediction_repository", fail)
    monkeypatch.setattr("app.main.latest_trading_day", lambda _: date(2026, 10, 6))

    response = TestClient(app).get("/predictions")

    assert response.status_code == 503
    assert "Tahmin kayıtları alınamadı" in response.json()["detail"]


def test_performance_api_exposes_evaluated_history(monkeypatch):
    class Repo:
        def get_recent(self, limit=100):
            return [
                SimpleNamespace(
                    symbol="EVAL",
                    prediction_date=date(2026, 10, 5),
                    target_date=date(2026, 10, 6),
                    probability_above_5=0.72,
                    expected_change_percent=5.4,
                    actual_change_percent=6.3,
                    successful=True,
                    model_version="v1",
                ),
                SimpleNamespace(
                    symbol="PENDING",
                    prediction_date=date(2026, 10, 6),
                    target_date=date(2026, 10, 7),
                    probability_above_5=0.61,
                    expected_change_percent=4.1,
                    actual_change_percent=None,
                    successful=None,
                    model_version="v1",
                ),
            ]

    monkeypatch.setattr("app.main.get_prediction_repository", lambda: Repo())
    response = TestClient(app).get("/performance?limit=30")

    assert response.status_code == 200
    payload = response.json()
    assert payload["tracked_count"] == 2
    assert payload["evaluated_count"] == 1
    assert payload["pending_count"] == 1
    assert payload["predictions"][0]["symbol"] == "EVAL"
    assert payload["predictions"][0]["actual_change_percent"] == 6.3
    assert payload["predictions"][0]["successful"] is True
