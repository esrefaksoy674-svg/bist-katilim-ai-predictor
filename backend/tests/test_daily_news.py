from datetime import date

from app.services import daily_news


def test_daily_news_collection_filters_for_date_and_persists(monkeypatch):
    captured = {}
    items = [{"symbol": "THYAO", "content_hash": "h1", "source": "kap_public"}]
    monkeypatch.setattr(
        daily_news,
        "collect_configured_news",
        lambda **kwargs: captured.update(kwargs) or {
            "source_count": 5,
            "reachable_sources": 5,
            "item_count": 1,
            "items": items,
            "sources": [],
        },
    )

    class Repository:
        def save_many(self, rows):
            captured["saved_items"] = rows
            return len(rows)

    monkeypatch.setattr(
        daily_news,
        "get_news_repository",
        lambda: Repository(),
    )

    result = daily_news.run_daily_news_collection(
        ["THYAO", "TUPRS"],
        date(2026, 10, 1),
    )

    assert captured["symbols"] == ["THYAO", "TUPRS"]
    assert captured["published_on"] == date(2026, 10, 1)
    assert captured["saved_items"] == items
    assert result["persisted_count"] == 1
    assert result["features_by_symbol"]["THYAO"] == {
        "article_count": 1,
        "source_count": 1,
        "kap_article_count": 1,
        "rss_article_count": 0,
    }
