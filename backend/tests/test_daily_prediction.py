from datetime import date
from types import SimpleNamespace

import pandas as pd
import pytest

from app.services.daily_prediction import run_daily_prediction
from app.services.model_registry import ModelRegistry


def test_daily_prediction_uses_active_model_and_universe(monkeypatch):
    registry = ModelRegistry()
    artifact = object()
    registry.register_shadow(
        "v1",
        artifact=artifact,
        accuracy=0.8,
    )
    registry.activate("v1")

    captured = {}

    monkeypatch.setattr(
        "app.services.daily_prediction.fetch_katilim_universe",
        lambda: ["THYAO", "TUPRS"],
    )
    monkeypatch.setattr(
        "app.services.daily_prediction.run_prediction_scan",
        lambda **kwargs: (
            captured.update(kwargs)
            or [SimpleNamespace(symbol="THYAO")]
        ),
    )

    result = run_daily_prediction(
        prediction_date=date(2026, 9, 28),
        registry=registry,
        history=pd.DataFrame(),
    )

    assert result.model_version == "v1"
    assert result.universe_count == 2
    assert result.predictions[0].symbol == "THYAO"
    assert captured["trained_model"] is artifact
    assert captured["symbols"] == ["THYAO", "TUPRS"]


def test_daily_prediction_rejects_missing_active_model():
    with pytest.raises(RuntimeError, match="Aktif model"):
        run_daily_prediction(
            prediction_date=date(2026, 9, 28),
            registry=ModelRegistry(),
            history=pd.DataFrame(),
        )


def test_daily_prediction_rejects_active_model_without_artifact():
    registry = ModelRegistry()
    registry.register_shadow("v1")
    registry.activate("v1")

    with pytest.raises(RuntimeError, match="artefaktı"):
        run_daily_prediction(
            prediction_date=date(2026, 9, 28),
            registry=registry,
            history=pd.DataFrame(),
        )
