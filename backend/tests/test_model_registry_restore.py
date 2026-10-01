from app.services.model_registry import ModelRegistry
from app.services.model_version_repository import restore_registry


class FakeRepository:
    def __init__(self, models):
        self.models = models

    def all(self):
        return self.models


class FakeArtifacts:
    def load(self, version):
        return {"version": version}


def test_restore_registry_loads_active_model_and_artifact():
    source = ModelRegistry()
    model = source.register_shadow("v1", accuracy=0.8, sample_count=10, artifact={"runtime": True})
    source.activate(model.version)

    target = ModelRegistry()
    restore_registry(target, FakeRepository(source.all()), FakeArtifacts())

    restored = target.active()
    assert restored is not None
    assert restored.version == "v1"
    assert restored.artifact == {"version": "v1"}
