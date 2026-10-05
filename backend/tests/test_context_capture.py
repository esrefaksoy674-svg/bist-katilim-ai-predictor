from datetime import date

import pandas as pd

from app.services import prediction_scan


def test_context_snapshot_store_failure_does_not_interrupt_prediction(monkeypatch):
    monkeypatch.setattr(
        prediction_scan,
        "build_candidate_features",
        lambda symbols, prediction_date: pd.DataFrame({
            "symbol": ["AAA"],
            "momentum": [1.0],
        }),
    )
    monkeypatch.setattr(prediction_scan, "build_predictions", lambda **kwargs: [])

    class BrokenRepository:
        def save_many(self, snapshots):
            raise RuntimeError("table migration is pending")

    status = {}
    result = prediction_scan.run_prediction_scan(
        symbols=["AAA"],
        prediction_date=date(2026, 10, 2),
        trained_model=object(),
        model_version="active",
        history=pd.DataFrame(),
        context_snapshot_repository=BrokenRepository(),
        context_snapshot_status=status,
    )

    assert result == []
    assert status == {"status": "unavailable", "error": "RuntimeError"}
