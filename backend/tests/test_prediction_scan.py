from datetime import date

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
            type(
                "Result",
                (),
                {
                    "symbol": "THYAO",
                    "prediction_date": date(2026, 9, 28),
                    "probability_above_5": 0.7,
                    "expected_change_percent": 6.0,
                    "model_confidence": 0.8,
                    "pattern_count": 5,
                    "explanation": {},
                    "model_version": "v1",
                },
            )()
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
    assert predictions[0].target_date == date(2026, 9, 28)


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
            type(
                "Result",
                (),
                {
                    "symbol": "THYAO",
                    "prediction_date": date(2026, 9, 28),
                    "probability_above_5": 0.7,
                    "expected_change_percent": 6.0,
                    "model_confidence": 0.8,
                    "pattern_count": 5,
                    "explanation": {},
                    "model_version": "v1",
                },
            )()
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
