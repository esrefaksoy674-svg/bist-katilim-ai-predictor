from datetime import date

import pandas as pd
import pytest

from app.services.contextual_dataset import merge_point_in_time_context


def test_context_merge_uses_only_strictly_prior_snapshots_and_namespaces_features():
    examples = pd.DataFrame({
        "symbol": ["AAA", "AAA", "BBB"],
        "reference_date": [date(2026, 1, 3), date(2026, 1, 5), date(2026, 1, 5)],
        "target": [1, 0, 1],
    })
    contexts = {
        "news": pd.DataFrame({
            "symbol": ["AAA", "AAA", "AAA", "BBB"],
            "available_date": [date(2026, 1, 2), date(2026, 1, 3), date(2026, 1, 6), date(2026, 1, 4)],
            "sentiment_score": [0.4, 0.9, -0.8, 0.2],
            "article_count": [2, 8, 3, 1],
        })
    }

    result = merge_point_in_time_context(examples, contexts)

    assert result["news__sentiment_score"].tolist() == [0.4, 0.9, 0.2]
    assert result["news__article_count"].tolist() == [2, 8, 1]
    assert result["target"].tolist() == [1, 0, 1]


def test_context_merge_leaves_missing_history_null():
    examples = pd.DataFrame({
        "symbol": ["AAA"],
        "reference_date": [date(2026, 1, 2)],
    })
    context = pd.DataFrame({
        "symbol": ["AAA"],
        "available_date": [date(2026, 1, 2)],
        "sector_return": [3.5],
    })

    result = merge_point_in_time_context(examples, {"sector": context})

    assert pd.isna(result.loc[0, "sector__sector_return"])


def test_context_merge_rejects_outcome_leakage_and_duplicate_snapshots():
    examples = pd.DataFrame({"symbol": ["AAA"], "reference_date": [date(2026, 1, 3)]})
    leaked = pd.DataFrame({
        "symbol": ["AAA"], "available_date": [date(2026, 1, 2)],
        "target": [1],
    })
    with pytest.raises(ValueError, match="Outcome columns"):
        merge_point_in_time_context(examples, {"market": leaked})

    duplicate = pd.DataFrame({
        "symbol": ["AAA", "AAA"],
        "available_date": [date(2026, 1, 2), date(2026, 1, 2)],
        "market_return": [1.0, 2.0],
    })
    with pytest.raises(ValueError, match="one aggregated row"):
        merge_point_in_time_context(examples, {"market": duplicate})
