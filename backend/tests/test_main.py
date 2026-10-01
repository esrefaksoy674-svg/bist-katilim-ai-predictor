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


def test_health_self_test_reports_universe_failure(monkeypatch):
    monkeypatch.setattr(
        "app.main.fetch_katilim_universe",
        lambda: (_ for _ in ()).throw(RuntimeError("source down")),
    )

    response = client.get("/health/self-test")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["universe_source"] is False
