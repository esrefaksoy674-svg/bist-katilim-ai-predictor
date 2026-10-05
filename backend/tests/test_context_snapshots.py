from datetime import date

import pandas as pd

from app.services.context_snapshots import (
    aggregate_news_features,
    build_context_snapshots,
    parse_sector_map,
)


def test_daily_context_snapshot_aggregates_market_sector_and_news_counts():
    candidates = pd.DataFrame({
        "symbol": ["AAA", "BBB", "CCC"],
        "momentum": [2.0, -1.0, 1.0],
        "rsi": [60.0, 42.0, 55.0],
    })
    news = aggregate_news_features([
        {"symbol": "AAA", "source": "kap_public", "content_hash": "1"},
        {"symbol": "AAA", "source": "rss", "content_hash": "2"},
        {"symbol": "AAA", "source": "rss", "content_hash": "2"},
    ])
    snapshots = build_context_snapshots(
        candidates,
        date(2026, 10, 5),
        news_features_by_symbol=news,
        sector_by_symbol={"AAA": "ENERGY", "BBB": "ENERGY"},
    )

    assert len(snapshots) == 3
    assert snapshots[0]["news_features"]["article_count"] == 2
    assert snapshots[0]["news_features"]["kap_article_count"] == 1
    assert snapshots[0]["market_features"]["universe_size"] == 3
    assert snapshots[0]["market_features"]["positive_momentum_share"] == 2 / 3
    assert snapshots[0]["sector_features"]["peer_count"] == 1
    assert snapshots[0]["sector_features"]["peer_momentum_mean_10d"] == -1.0
    assert snapshots[2]["sector_features"] == {}


def test_sector_map_parser_ignores_invalid_entries_and_normalizes_symbols():
    assert parse_sector_map(" aaA:Energy, broken,BBB:BANK ") == {
        "AAA": "ENERGY",
        "BBB": "BANK",
    }
