from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_returns_timestamp():
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert "timestamp" in body


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


def test_health_self_test_reports_pipeline_failures_without_exposing_error(monkeypatch):
    monkeypatch.setattr("app.main.check_runtime_configuration", lambda: True)
    monkeypatch.setattr("app.main.check_pipeline_imports", lambda: True)
    monkeypatch.setattr(
        "app.main.fetch_katilim_universe",
        lambda: (_ for _ in ()).throw(RuntimeError("secret provider response")),
    )
    monkeypatch.setattr(
        "app.main.fetch_daily_data",
        lambda *args, **kwargs: [{"close": 1}],
    )
    monkeypatch.setattr(
        "app.main.get_prediction_repository",
        lambda: type("Repository", (), {"get_by_date": lambda self, value: []})(),
    )

    response = client.get("/health/self-test")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["api"] is True
    assert body["checks"]["universe_source"] is False
    assert body["checks"]["market_data_source"] is True
    assert body["checks"]["persistence_read"] is True
    assert body["errors"]["universe_source"] == {"type": "RuntimeError"}
    assert "secret provider response" not in response.text


def test_health_self_test_passes_when_read_only_dependencies_are_available(monkeypatch):
    monkeypatch.setattr("app.main.check_runtime_configuration", lambda: True)
    monkeypatch.setattr("app.main.check_pipeline_imports", lambda: True)
    monkeypatch.setattr("app.main.fetch_katilim_universe", lambda: ["THYAO"])
    monkeypatch.setattr("app.main.fetch_daily_data", lambda *args, **kwargs: [1, 2])
    monkeypatch.setattr(
        "app.main.get_prediction_repository",
        lambda: type("Repository", (), {"get_by_date": lambda self, value: []})(),
    )

    response = client.get("/health/self-test")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert all(body["checks"].values())
    assert body["errors"] == {}
