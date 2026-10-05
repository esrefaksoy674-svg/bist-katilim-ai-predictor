from datetime import date

from app.services import daily_scan


def test_daily_scan_builds_history_and_runs_prediction(monkeypatch):
    calls = {}
    monkeypatch.setattr(daily_scan, "fetch_katilim_universe", lambda: ["AAA", "BBB"])
    monkeypatch.setattr(daily_scan, "run_daily_learning", lambda **kwargs: {"created": 2})
    monkeypatch.setattr(daily_scan, "load_active_model", lambda: ("REGISTRY", "ARTIFACT"))
    monkeypatch.setattr(
        daily_scan,
        "build_prediction_history",
        lambda **kwargs: calls.update(history_kwargs=kwargs) or "HISTORY",
    )
    monkeypatch.setattr(daily_scan, "get_prediction_repository", lambda: "REPOSITORY")
    monkeypatch.setattr(daily_scan, "get_context_snapshot_repository", lambda: "CONTEXT_REPOSITORY")
    monkeypatch.setattr(
        daily_scan,
        "run_daily_prediction",
        lambda **kwargs: calls.update(prediction_kwargs=kwargs) or "PREDICTIONS",
    )
    monkeypatch.setattr(
        daily_scan,
        "run_daily_news_collection",
        lambda **kwargs: {
            "item_count": 2,
            "persisted_count": 2,
            "features_by_symbol": {"AAA": {"article_count": 2}},
        },
    )

    result = daily_scan.run_daily_scan(
        trading_date=date(2026, 10, 2),
        learning_enabled=True,
        top_n=10,
    )

    assert result["universe_count"] == 2
    assert result["learning"] == {"created": 2}
    assert result["predictions"] == "PREDICTIONS"
    assert result["news"]["persisted_count"] == 2
    assert result["trading_date"] == "2026-10-02"
    assert result["target_date"] == "2026-10-05"
    assert calls["history_kwargs"]["prediction_date"] == date(2026, 10, 2)
    assert calls["prediction_kwargs"]["history"] == "HISTORY"
    assert calls["prediction_kwargs"]["symbols"] == ["AAA", "BBB"]
    assert calls["prediction_kwargs"]["top_n"] == 10
    assert calls["prediction_kwargs"]["target_date"] == date(2026, 10, 5)
    assert calls["prediction_kwargs"]["context_snapshot_repository"] == "CONTEXT_REPOSITORY"
    assert calls["prediction_kwargs"]["news_features_by_symbol"]["AAA"]["article_count"] == 2
    assert result["context_snapshots"]["status"] == "pending"


def test_daily_scan_can_skip_learning(monkeypatch):
    monkeypatch.setattr(daily_scan, "fetch_katilim_universe", lambda: ["AAA"])
    monkeypatch.setattr(daily_scan, "load_active_model", lambda: ("REGISTRY", "ARTIFACT"))
    monkeypatch.setattr(daily_scan, "build_prediction_history", lambda **kwargs: "HISTORY")
    monkeypatch.setattr(daily_scan, "get_prediction_repository", lambda: "REPOSITORY")
    monkeypatch.setattr(daily_scan, "run_daily_prediction", lambda **kwargs: "PREDICTIONS")
    monkeypatch.setattr(daily_scan, "run_daily_news_collection", lambda **kwargs: {"persisted_count": 0})

    def fail_learning(**kwargs):
        raise AssertionError("Learning must be skipped")

    monkeypatch.setattr(daily_scan, "run_daily_learning", fail_learning)

    result = daily_scan.run_daily_scan(
        trading_date=date(2026, 10, 2),
        learning_enabled=False,
    )

    assert result["learning"] is None
    assert result["predictions"] == "PREDICTIONS"
