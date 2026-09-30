from app.core.health import get_health_status


def test_health_status():
    result = get_health_status()

    assert result["status"] == "healthy"
    assert result["service"] == "bist-katilim-ai-predictor"
    assert result["timestamp"]
