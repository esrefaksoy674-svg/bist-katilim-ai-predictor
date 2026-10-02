from io import BytesIO
import joblib
from app.services.model_artifact_repository import SupabaseStorageModelArtifactRepository

class FakeStorageBucket:
    def __init__(self): self.payloads = {}
    def upload(self, path, payload, options): self.payloads[path] = payload
    def download(self, path): return self.payloads[path]

class FakeStorage:
    def __init__(self): self.bucket = FakeStorageBucket()
    def from_(self, bucket_name):
        assert bucket_name == "model-artifacts"
        return self.bucket

class FakeClient:
    def __init__(self): self.storage = FakeStorage()

def test_model_artifact_round_trip_uses_compression():
    client = FakeClient()
    repository = SupabaseStorageModelArtifactRepository(client)
    artifact = {"version": "v1", "values": [1, 2, 3] * 10_000}

    repository.save("v1", artifact)
    payload = client.storage.bucket.payloads["v1.joblib"]
    uncompressed = BytesIO()
    joblib.dump(artifact, uncompressed, compress=0)

    assert len(payload) < len(uncompressed.getvalue())
    assert repository.load("v1") == artifact
