from datetime import datetime, timezone

from app.core.news_sources import get_enabled_sources
from app.services import news, news_ingestion


def test_configured_sources_parse_urls(monkeypatch):
    from app.core.news_sources import settings

    monkeypatch.setattr(settings, "news_rss_urls", "https://example.com/news.xml, https://example.com/news.xml")
    monkeypatch.setattr(settings, "kap_rss_urls", "")
    sources = get_enabled_sources()

    assert sources["news"]["enabled"] is True
    assert sources["news"]["urls"] == ["https://example.com/news.xml"]
    assert sources["kap"]["enabled"] is False


def test_fetch_rss_uses_timeout_and_normalizes_feed(monkeypatch):
    class Response:
        content = b"<rss/>"

        @staticmethod
        def raise_for_status():
            pass

    captured = {}
    monkeypatch.setattr(
        news.requests,
        "get",
        lambda url, **kwargs: captured.update(url=url, **kwargs) or Response(),
    )
    monkeypatch.setattr(
        news.feedparser,
        "parse",
        lambda content: type(
            "Feed",
            (),
            {
                "bozo": False,
                "entries": [
                    {
                        "title": "THYAO KAP bildirimi",
                        "link": "https://example.com/1",
                        "published_parsed": (2026, 10, 1, 9, 0, 0, 3, 274, 0),
                    }
                ],
            },
        )(),
    )

    result = news.fetch_rss("https://example.com/rss", timeout=7)

    assert captured["timeout"] == 7
    assert captured["headers"]["User-Agent"]
    assert result[0]["source"] == "example.com"
    assert result[0]["published_at"].tzinfo == timezone.utc


def test_collect_configured_news_deduplicates_filters_and_hides_source_errors(monkeypatch):
    monkeypatch.setattr(
        news_ingestion,
        "get_enabled_sources",
        lambda: {
            "news": {"enabled": True, "urls": ["https://safe.example/rss", "https://secret.example/rss"]},
            "kap": {"enabled": False, "urls": []},
        },
    )
    item = {
        "title": "THYAO yatırım anlaşması",
        "url": "https://example.com/article",
        "source": "example.com",
        "published_at": datetime(2026, 10, 1, tzinfo=timezone.utc),
        "content_hash": "same",
    }

    def fake_fetch(url, timeout):
        if "secret" in url:
            raise RuntimeError("private token detail")
        return [item, dict(item)]

    monkeypatch.setattr(news_ingestion, "fetch_rss", fake_fetch)
    result = news_ingestion.collect_configured_news(["THYAO"])

    assert result["source_count"] == 2
    assert result["reachable_sources"] == 1
    assert result["item_count"] == 1
    assert result["items"][0]["symbol"] == "THYAO"
    assert result["sources"][1]["error"] == "RuntimeError"
    assert "private token detail" not in str(result)
