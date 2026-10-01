from datetime import timezone

import pytest

from app.services import kap_public


SAMPLE_HTML = """
<html><body>
<a href="/tr/Bildirim/12345">Özel Durum Açıklaması</a>
<p>Şirketimiz hakkında açıklama</p>
<span>Gönderim Tarihi</span><span>01/10/2026 14:30:00</span>
<a href="/tr/Bildirim/12346">Finansal Rapor Bildirimi</a>
<span>Gönderim Tarihi</span><span>30/09/2026 18:05</span>
</body></html>
"""


def test_parse_public_search_results_extracts_links_titles_and_dates():
    items = kap_public._parse_search_page(SAMPLE_HTML, "THYAO")

    assert len(items) == 2
    assert items[0]["symbol"] == "THYAO"
    assert items[0]["title"] == "Özel Durum Açıklaması"
    assert items[0]["url"] == "https://www.kap.org.tr/tr/Bildirim/12345"
    assert items[0]["published_at"].tzinfo == timezone.utc
    assert items[0]["published_at"].hour == 11
    assert items[1]["published_at"].hour == 15


def test_public_search_rejects_invalid_symbols_before_network(monkeypatch):
    monkeypatch.setattr(
        kap_public.requests,
        "get",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("invalid symbol must not make a request")
        ),
    )

    with pytest.raises(ValueError):
        kap_public.fetch_kap_public_search("../THYAO")


def test_public_search_uses_timeout_and_caches_per_symbol(monkeypatch):
    kap_public._cache.clear()
    calls = []

    class Response:
        text = SAMPLE_HTML

        @staticmethod
        def raise_for_status():
            pass

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        return Response()

    monkeypatch.setattr(kap_public.requests, "get", fake_get)

    first = kap_public.fetch_kap_public_search("THYAO")
    second = kap_public.fetch_kap_public_search("THYAO")

    assert len(first) == 2
    assert second == first
    assert len(calls) == 1
    assert calls[0][1]["timeout"] == kap_public.REQUEST_TIMEOUT_SECONDS
    assert "/tr/search/THYAO/1" in calls[0][0]
    kap_public._cache.clear()
