from datetime import datetime, timezone


def get_health_status() -> dict:
    return {
        "status": "healthy",
        "service": "bist-katilim-ai-predictor",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
