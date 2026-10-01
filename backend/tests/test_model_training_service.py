from datetime import date

import pytest

from app.services import model_training_service


def test_training_service_blocks_when_learning_disabled(monkeypatch):
    monkeypatch.setattr(
        model_training_service.learning_control,
        "can_learn",
        lambda: False,
    )

    with pytest.raises(RuntimeError, match="Öğrenme kapalı"):
        model_training_service.train_and_persist_market_model(
            version="test-1",
            registry=object(),
        )


def test_training_service_uses_universe_and_persists(monkeypatch):
    calls = {}

    monkeypatch.setattr(
        model_training_service.learning_control,
        "can_learn",
        lambda: True,
    )
    monkeypatch.setattr(
        model_training_service,
        "fetch_katilim_universe",
        lambda: ["AAA", "BBB"],
    )
    monkeypatch.setattr(
        model_training_service,
        "get_model_version_repository",
        lambda: object(),
    )
    monkeypatch.setattr(
        model_training_service,
        "get_model_artifact_repository",
        lambda: object(),
    )
    monkeypatch.setattr(
        model_training_service,
        "train_from_market_history",
        lambda **kwargs: calls.update(kwargs) or "RESULT",
    )
    monkeypatch.setattr(
        model_training_service,
        "persist_models",
        lambda registry, repository: calls.update(
            persisted=(registry, repository)
        ),
    )

    result = model_training_service.train_and_persist_market_model(
        version="test-2",
        registry="REGISTRY",
        cutoff_date=date(2026, 9, 28),
        validation_ratio=0.25,
        promote=False,
        min_history=180,
    )

    assert result == "RESULT"
    assert calls["symbols"] == ["AAA", "BBB"]
    assert calls["version"] == "test-2"
    assert calls["cutoff_date"] == date(2026, 9, 28)
    assert calls["validation_ratio"] == 0.25
    assert calls["promote"] is False
    assert calls["min_history"] == 180
    assert calls["persisted"][0] == "REGISTRY"
