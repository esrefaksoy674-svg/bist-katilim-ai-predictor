from datetime import date, datetime, timezone

from app.models.learning_event import LearningEvent
from app.services.learning_memory_repository import (
    SupabaseLearningEventRepository,
)


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    def __init__(self, table):
        self.table = table
        self.filters = []
        self.operation = None
        self.payload = None

    def upsert(self, payload, on_conflict=None):
        self.operation = "upsert"
        self.payload = payload
        self.on_conflict = on_conflict
        return self

    def select(self, value):
        self.operation = "select"
        return self

    def order(self, column):
        self.order_column = column
        return self

    def lt(self, column, value):
        self.filters.append((column, value))
        return self

    def execute(self):
        if self.operation == "upsert":
            self.table.rows.append(self.payload)
            return FakeResponse([self.payload])
        return FakeResponse(self.table.rows)


class FakeTable:
    def __init__(self):
        self.rows = []
        self.last_query = None

    def table_query(self):
        self.last_query = FakeQuery(self)
        return self.last_query


class FakeClient:
    def __init__(self):
        self.store = FakeTable()

    def table(self, name):
        assert name == "learning_events"
        return self.store.table_query()


def make_event():
    return LearningEvent(
        symbol="THYAO",
        signal_date=date(2026, 9, 28),
        reference_date=date(2026, 9, 25),
        rise_percent=5.5,
        technical_features={"rsi": 60},
        news_features={"positive": 1},
        sector_features={},
        source_quality=0.9,
        created_at=datetime(2026, 9, 28, tzinfo=timezone.utc),
    )


def test_repository_maps_event_to_supabase_row():
    client = FakeClient()
    repository = SupabaseLearningEventRepository(client)

    repository.add(make_event())

    assert len(client.store.rows) == 1
    row = client.store.rows[0]
    assert row["symbol"] == "THYAO"
    assert row["signal_date"] == "2026-09-28"
    assert row["rise_percent"] == 5.5


def test_repository_round_trips_event():
    client = FakeClient()
    repository = SupabaseLearningEventRepository(client)

    event = make_event()
    repository.add(event)

    result = repository.all()

    assert len(result) == 1
    assert result[0].symbol == event.symbol
    assert result[0].signal_date == event.signal_date
    assert result[0].rise_percent == event.rise_percent
    assert result[0].technical_features == event.technical_features


def test_repository_filters_before_target_date():
    client = FakeClient()
    repository = SupabaseLearningEventRepository(client)

    repository.add(make_event())

    result = repository.get_before(date(2026, 9, 29))

    assert len(result) == 1
    assert result[0].signal_date < date(2026, 9, 29)
