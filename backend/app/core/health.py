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
    """Validate required runtime settings without exposing credential values."""
    if not all(
        value.strip()
        for value in (settings.app_name, settings.app_version, settings.environment)
    ):
        return False

    if not settings.supabase_url.strip() or not settings.supabase_key.strip():
        return False

    parsed_url = urlparse(settings.supabase_url.strip())
    if parsed_url.scheme != "https" or not parsed_url.hostname:
        return False

    # Credentials embedded in a URL are easy to leak through diagnostics/logs.
    if parsed_url.username or parsed_url.password:
        return False

    return True


def check_pipeline_imports() -> bool:
    """Confirm that runtime packages used by critical pipelines are installed."""
    return all(find_spec(module) is not None for module in REQUIRED_PIPELINE_MODULES)
