from datetime import date, datetime, timezone

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
    monkeypatch.setattr(news_ingestion, "fetch_kap_public_search", lambda symbol: [])

    def fake_fetch(url, timeout):
        if "secret" in url:
            raise RuntimeError("private token detail")
        return [item, dict(item)]

    monkeypatch.setattr(news_ingestion, "fetch_rss", fake_fetch)
    result = news_ingestion.collect_configured_news(["THYAO"])

    assert result["source_count"] == 3
    assert result["reachable_sources"] == 2
    assert result["item_count"] == 1
    assert result["items"][0]["symbol"] == "THYAO"
    assert result["sources"][1]["error"] == "RuntimeError"
    assert "private token detail" not in str(result)


def test_collect_configured_news_queries_each_ticker_and_filters_eod(monkeypatch):
    monkeypatch.setattr(news_ingestion, "get_enabled_sources", lambda: {})
    requested = []

    def fake_kap(symbol):
        requested.append(symbol)
        return [{
            "title": f"{symbol} bildirimi",
            "url": f"https://www.kap.org.tr/tr/Bildirim/{symbol}",
            "source": "kap.org.tr",
            "published_at": datetime(2026, 10, 1, 12, tzinfo=timezone.utc),
            "content_hash": symbol,
            "symbol": symbol,
        }, {
            "title": f"{symbol} eski bildirim",
            "url": f"https://www.kap.org.tr/tr/Bildirim/old-{symbol}",
            "source": "kap.org.tr",
            "published_at": datetime(2026, 9, 30, 12, tzinfo=timezone.utc),
            "content_hash": f"old-{symbol}",
            "symbol": symbol,
        }]

    monkeypatch.setattr(news_ingestion, "fetch_kap_public_search", fake_kap)
    result = news_ingestion.collect_configured_news(
        ["THYAO", "TUPRS"],
        published_on=date(2026, 10, 1),
    )

    assert requested == ["THYAO", "TUPRS"]
    assert result["item_count"] == 2
    assert {item["symbol"] for item in result["items"]} == {"THYAO", "TUPRS"}
    assert all(item["content_hash"] in requested for item in result["items"])
