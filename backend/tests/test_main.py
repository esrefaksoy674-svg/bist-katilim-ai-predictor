from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


client = TestClient(app)


def test_health_returns_timestamp():
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert "timestamp" in body


def test_dashboard_serves_prediction_panel():
    response = client.get("/dashboard")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "BIST Katılım Tahminleri" in response.text
    assert 'fetch("/predictions" + query' in response.text


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_universe_endpoint_returns_service_unavailable_on_source_error(monkeypatch):
    monkeypatch.setattr(
        "app.main.fetch_katilim_universe",
        lambda: (_ for _ in ()).throw(RuntimeError("source down")),
    )

    response = client.get("/universe")

    assert response.status_code == 503


def test_health_self_test_requires_configured_token(monkeypatch):
    monkeypatch.setattr(settings, "self_test_token", "")

    response = client.get("/health/self-test")

    assert response.status_code == 503


def test_health_self_test_rejects_missing_or_invalid_token(monkeypatch):
    monkeypatch.setattr(settings, "self_test_token", "configured-secret")

    assert client.get("/health/self-test").status_code == 401
    assert client.get(
        "/health/self-test",
        headers={"X-Self-Test-Token": "wrong-secret"},
    ).status_code == 401


def test_health_self_test_reports_pipeline_failures_without_exposing_error(monkeypatch):
    monkeypatch.setattr(settings, "self_test_token", "configured-secret")
    monkeypatch.setattr("app.main.check_runtime_configuration", lambda: True)
    monkeypatch.setattr("app.main.check_pipeline_imports", lambda: True)
    monkeypatch.setattr(
        "app.main.fetch_katilim_universe",
        lambda: (_ for _ in ()).throw(RuntimeError("secret provider response")),
    )
    monkeypatch.setattr("app.main.fetch_daily_data", lambda *args, **kwargs: [{"close": 1}])
    monkeypatch.setattr(
        "app.main.get_prediction_repository",
        lambda: type("Repository", (), {"get_by_date": lambda self, value: []})(),
    )

    response = client.get(
        "/health/self-test",
        headers={"X-Self-Test-Token": "configured-secret"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["api"] is True
    assert body["checks"]["universe_source"] is False
    assert body["checks"]["market_data_source"] is True
    assert body["checks"]["persistence_read"] is True
    assert body["errors"]["universe_source"] == {"type": "RuntimeError"}
    assert "secret provider response" not in response.text


def test_health_self_test_passes_with_read_only_dependency_checks(monkeypatch):
    monkeypatch.setattr(settings, "self_test_token", "configured-secret")
    monkeypatch.setattr("app.main.check_runtime_configuration", lambda: True)
    monkeypatch.setattr("app.main.check_pipeline_imports", lambda: True)
    monkeypatch.setattr("app.main.fetch_katilim_universe", lambda: ["THYAO"])
    monkeypatch.setattr("app.main.fetch_daily_data", lambda *args, **kwargs: [1, 2])
    monkeypatch.setattr(
        "app.main.get_prediction_repository",
        lambda: type("Repository", (), {"get_by_date": lambda self, value: []})(),
    )

    response = client.get(
        "/health/self-test",
        headers={"X-Self-Test-Token": "configured-secret"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert all(body["checks"].values())
    assert body["errors"] == {}
    assert body["checked_at"]
    assert body["duration_ms"] >= 0
    assert set(body["check_durations_ms"]) == {
        "universe_source",
        "market_data_source",
        "persistence_read",
    }
    assert all(duration >= 0 for duration in body["check_durations_ms"].values())


def test_news_endpoint_returns_configured_ingestion_result(monkeypatch):
    monkeypatch.setattr(
        "app.main.collect_configured_news",
        lambda symbols: {"item_count": 1, "items": [{"symbol": symbols[0]}]},
    )

    response = client.get("/news?symbol=thyao")

    assert response.status_code == 200
    assert response.json()["items"][0]["symbol"] == "THYAO"


def test_predictions_endpoint_keeps_high_probability_candidate_below_five_mean(monkeypatch):
    from datetime import date
    from types import SimpleNamespace

    rows = [
        SimpleNamespace(
            target_date=date(2026, 10, 5),
            expected_change_percent=4.2,
            probability_above_5=0.91,
            symbol="THYAO",
            model_confidence=0.8,
            pattern_count=12,
            explanation={},
            model_version="v1",
            actual_change_percent=None,
            successful=None,
            evaluated_at=None,
        ),
        SimpleNamespace(
            target_date=date(2026, 10, 5),
            expected_change_percent=6.0,
            probability_above_5=0.72,
            symbol="ASELS",
            model_confidence=0.8,
            pattern_count=10,
            explanation={},
            model_version="v1",
            actual_change_percent=None,
            successful=None,
            evaluated_at=None,
        ),
    ]
    monkeypatch.setattr(
        "app.main.get_prediction_repository",
        lambda: type("Repository", (), {"get_latest_date": lambda self: date(2026, 10, 2), "get_by_date": lambda self, value: rows})(),
    )
    monkeypatch.setattr(
        "app.main.latest_trading_day",
        lambda value: date(2026, 10, 2),
    )
    monkeypatch.setattr(
        "app.main.next_trading_day",
        lambda value: date(2026, 10, 5),
    )

    response = client.get("/predictions?prediction_date=2026-10-02")

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 2
    assert body["predictions"][0]["expected_change_percent"] == 4.2
    assert body["predictions"][0]["probability_above_5"] == 0.91
