from datetime import datetime, timezone
from importlib.util import find_spec
from urllib.parse import urlparse

from app.core.config import settings


REQUIRED_PIPELINE_MODULES = (
    "fastapi",
    "pydantic",
    "pandas",
    "sklearn",
    "ta",
    "yfinance",
    "feedparser",
    "supabase",
)


def get_health_status() -> dict:
    return {
        "status": "healthy",
        "service": "bist-katilim-ai-predictor",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def check_runtime_configuration() -> bool:
    """Validate non-secret runtime settings without exposing credential values."""
    if not settings.app_name.strip() or not settings.app_version.strip():
        return False

    if not settings.environment.strip():
        return False

    if not settings.supabase_url or not settings.supabase_key:
        return False

    parsed_url = urlparse(settings.supabase_url)
    return parsed_url.scheme in {"https", "http"} and bool(parsed_url.netloc)


def check_pipeline_imports() -> bool:
    """Confirm that runtime packages used by critical pipelines are installed."""
    return all(find_spec(module) is not None for module in REQUIRED_PIPELINE_MODULES)
