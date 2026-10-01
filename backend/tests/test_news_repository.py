from datetime import datetime, timezone

from app.services.news_repository import SupabaseNewsRepository


class FakeQuery:
    def __init__(self, client):
        self.client = client

    def upsert(self, rows, on_conflict):
        self.client.calls.append((rows, on_conflict))
        return self

    def execute(self):
        return None


class FakeClient:
    def __init__(self):
        self.calls = []

    def table(self, table_name):
        assert table_name == "news_items"
        return FakeQuery(self)


def test_news_repository_upserts_normalized_idempotent_rows():
    client = FakeClient()
    repository = SupabaseNewsRepository(client)

    saved = repository.save_many(
        [{
            "symbol": "thyao",
            "title": "Bildirim",
            "url": "https://www.kap.org.tr/tr/Bildirim/123",
            "source": "kap.org.tr",
            "published_at": datetime(2026, 10, 1, tzinfo=timezone.utc),
            "content_hash": "digest",
        }]
    )

    assert saved == 1
    assert client.calls[0][1] == "symbol,content_hash"
    assert client.calls[0][0][0]["symbol"] == "THYAO"
