from datetime import date

import pandas as pd

from app.services.prediction_history import build_prediction_history


def test_prediction_history_excludes_prediction_date_and_future(monkeypatch):
    frame = pd.DataFrame(
        {
            "symbol": ["AAA", "AAA", "AAA"],
            "reference_date": [
                "2026-09-28",
                "2026-09-30",
                "2026-10-01",
            ],
            "target_date": [
                "2026-09-29",
                "2026-10-01",
                "2026-10-02",
            ],
            "target": [1, 0, 1],
            "actual_change_percent": [6.0, -1.0, 8.0],
            "rsi": [60, 55, 70],
        }
    )

    monkeypatch.setattr(
        "app.services.prediction_history.fetch_daily_data",
        lambda symbol, period="2y": pd.DataFrame({"Close": [1]}),
    )
    monkeypatch.setattr(
        "app.services.prediction_history.build_labeled_examples",
        lambda data, symbol, min_history: frame,
    )

    result = build_prediction_history(
        ["AAA"],
        prediction_date=date(2026, 10, 1),
        min_history=200,
    )

    assert result["reference_date"].tolist() == [
        "2026-09-28",
        "2026-09-30",
    ]
