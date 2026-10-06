from datetime import date
from types import SimpleNamespace

import pandas as pd

from app.services import prediction_scan


class DummyModel:
    pass


def test_prediction_scan_does_not_read_future_rows_for_target_date(monkeypatch):
    index = pd.to_datetime(
        [
            "2026-09-24",
            "2026-09-25",
            "2026-09-28",
            "2026-09-29",
        ]
    )
    data = pd.DataFrame(
        {
            "Open": [10, 11, 12, 13],
            "High": [11, 12, 13, 14],
            "Low": [9, 10, 11, 12],
            "Close": [10.5, 11.5, 12.5, 13.5],
            "Volume": [100, 110, 120, 130],
        },
        index=index,
    )

    monkeypatch.setattr(
        prediction_scan,
        "fetch_daily_data",
        lambda symbol, period="2y": data,
    )
    monkeypatch.setattr(
        prediction_scan,
        "calculate_features",
        lambda history: {name: 1.0 for name in prediction_scan.FEATURE_NAMES},
    )
    monkeypatch.setattr(
        prediction_scan,
        "build_predictions",
        lambda **kwargs: [
            SimpleNamespace(
                symbol="THYAO",
                prediction_date=date(2026, 9, 28),
                probability_above_5=0.7,
                expected_change_percent=6.0,
                model_confidence=0.8,
                pattern_count=5,
                explanation={},
                model_version="v1",
            )
        ],
    )

    predictions = prediction_scan.run_prediction_scan(
        symbols=["THYAO"],
        prediction_date=date(2026, 9, 28),
        trained_model=DummyModel(),
        model_version="v1",
        history=pd.DataFrame(),
    )

    assert len(predictions) == 1
    assert predictions[0].target_date == date(2026, 9, 29)


def test_prediction_scan_accepts_explicit_target_date(monkeypatch):
    index = pd.to_datetime(["2026-09-28"])
    data = pd.DataFrame(
        {
            "Open": [12],
            "High": [13],
            "Low": [11],
            "Close": [12.5],
            "Volume": [120],
        },
        index=index,
    )

    monkeypatch.setattr(
        prediction_scan,
        "fetch_daily_data",
        lambda symbol, period="2y": data,
    )
    monkeypatch.setattr(
        prediction_scan,
        "calculate_features",
        lambda history: {name: 1.0 for name in prediction_scan.FEATURE_NAMES},
    )
    monkeypatch.setattr(
        prediction_scan,
        "build_predictions",
        lambda **kwargs: [
            SimpleNamespace(
                symbol="THYAO",
                prediction_date=date(2026, 9, 28),
                probability_above_5=0.7,
                expected_change_percent=6.0,
                model_confidence=0.8,
                pattern_count=5,
                explanation={},
                model_version="v1",
            )
        ],
    )

    predictions = prediction_scan.run_prediction_scan(
        symbols=["THYAO"],
        prediction_date=date(2026, 9, 28),
        target_date=date(2026, 9, 29),
        trained_model=DummyModel(),
        model_version="v1",
        history=pd.DataFrame(),
    )

    assert predictions[0].target_date == date(2026, 9, 29)


def test_prediction_scan_filters_negative_expected_returns_and_keeps_list_selective(monkeypatch):
    monkeypatch.setattr(
        prediction_scan,
        "build_candidate_features",
        lambda symbols, prediction_date: pd.DataFrame({"symbol": symbols}),
    )
    monkeypatch.setattr(
        prediction_scan,
        "build_predictions",
        lambda **kwargs: [
            SimpleNamespace(
                symbol=symbol,
                prediction_date=date(2026, 10, 2),
                probability_above_5=probability,
                expected_change_percent=expected,
                model_confidence=0.8,
                pattern_count=5,
                explanation={},
                model_version="v1",
            )
            for symbol, probability, expected in [("LOW_EXPECTATION", 0.95, 4.99), ("EDGE", 0.20, 5.0), ("HIGH", 0.76, 6.1)]
        ],
    )
    persisted = []

    predictions = prediction_scan.run_prediction_scan(
        symbols=["LOW_EXPECTATION", "EDGE", "HIGH"],
        prediction_date=date(2026, 10, 2),
        target_date=date(2026, 10, 5),
        trained_model=DummyModel(),
        model_version="v1",
        history=pd.DataFrame(),
        prediction_repository=SimpleNamespace(add=persisted.append),
    )

    assert [prediction.symbol for prediction in predictions] == ["HIGH"]
    assert [prediction.symbol for prediction in persisted] == ["HIGH"]
    assert all(prediction.expected_change_percent > 0 for prediction in predictions)
    assert all(prediction.target_date == date(2026, 10, 5) for prediction in predictions)
