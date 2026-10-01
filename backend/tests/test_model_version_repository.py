from datetime import datetime, timezone

from app.services.model_registry import ModelRegistry
from app.services.model_version_repository import SupabaseModelVersionRepository


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows
        self.operation = None

    def upsert(self, row, on_conflict=None):
        self.operation = ("upsert", row, on_conflict)
        return self

    def select(self, value):
        self.operation = ("select", value)
        return self

    def eq(self, key, value):
        self.operation = ("eq", key, value)
        return self

    def limit(self, value):
        self.operation = ("limit", value)
        return self

    def order(self, value):
        self.operation = ("order", value)
        return self

    def execute(self):
        return FakeResponse(self.rows)


class FakeClient:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.last = None

    def table(self, name):
        self.last = FakeQuery(self.rows)
        return self.last


def test_model_version_repository_round_trip_mapping():
    registry = ModelRegistry()
    model = registry.register_shadow(
        version="v-test",
        accuracy=0.8,
        precision=0.75,
        recall=0.7,
        sample_count=100,
        pattern_count=25,
    )
    model.activated_at = datetime.now(timezone.utc)

    row = SupabaseModelVersionRepository._to_row(model)
    restored = SupabaseModelVersionRepository._from_row(row)

    assert restored.version == "v-test"
    assert restored.status == "SHADOW"
    assert restored.sample_count == 100
    assert restored.pattern_count == 25
    assert restored.accuracy == 0.8


def test_model_version_repository_add_and_get():
    registry = ModelRegistry()
    model = registry.register_shadow(version="v-test", sample_count=10)
    row = SupabaseModelVersionRepository._to_row(model)
    repo = SupabaseModelVersionRepository(FakeClient([row]))

    repo.add(model)
    restored = repo.get("v-test")

    assert restored is not None
    assert restored.version == "v-test"
