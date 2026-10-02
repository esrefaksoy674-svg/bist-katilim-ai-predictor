from app.core.health import check_pipeline_imports, check_runtime_configuration, get_health_status


def test_health_status():
    result = get_health_status()

    assert result["status"] == "healthy"
    assert result["service"] == "bist-katilim-ai-predictor"
    assert result["timestamp"]


def _configure_valid_runtime(monkeypatch):
    from app.core.health import settings

    monkeypatch.setattr(settings, "app_name", "BIST Predictor")
    monkeypatch.setattr(settings, "app_version", "0.1.0")
    monkeypatch.setattr(settings, "environment", "test")
    monkeypatch.setattr(settings, "supabase_url", "https://example.supabase.co")
    monkeypatch.setattr(settings, "supabase_key", "test-key")


def test_runtime_configuration_requires_supabase_credentials(monkeypatch):
    _configure_valid_runtime(monkeypatch)
    from app.core.health import settings

    monkeypatch.setattr(settings, "supabase_key", "")

    assert check_runtime_configuration() is False


def test_runtime_configuration_accepts_configured_supabase(monkeypatch):
    _configure_valid_runtime(monkeypatch)

    assert check_runtime_configuration() is True


def test_runtime_configuration_rejects_insecure_or_credential_bearing_url(monkeypatch):
    _configure_valid_runtime(monkeypatch)
    from app.core.health import settings

    monkeypatch.setattr(settings, "supabase_url", "http://example.supabase.co")
    assert check_runtime_configuration() is False

    monkeypatch.setattr(settings, "supabase_url", "https://user:password@example.supabase.co")
    assert check_runtime_configuration() is False


def test_pipeline_import_check_reports_missing_module(monkeypatch):
    import app.core.health as health

    monkeypatch.setattr(health, "find_spec", lambda module: None if module == "ta" else object())

    assert check_pipeline_imports() is False
