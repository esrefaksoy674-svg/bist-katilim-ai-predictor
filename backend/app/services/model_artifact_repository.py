from __future__ import annotations

from io import BytesIO
from typing import Any

import joblib


class ModelArtifactRepository:
    """Eğitilmiş sklearn model artefaktlarını kalıcı depolama katmanına bağlar."""

    def save(self, version: str, artifact: Any) -> None:
        raise NotImplementedError

    def load(self, version: str) -> Any:
        raise NotImplementedError


class SupabaseStorageModelArtifactRepository(ModelArtifactRepository):
    bucket_name = "model-artifacts"

    def __init__(self, client: Any):
        self.client = client

    @staticmethod
    def _serialize(artifact: Any) -> bytes:
        buffer = BytesIO()
        # Random-forest artifacts can exceed Supabase Free's 50 MB upload limit
        # when stored uncompressed. joblib.load detects the compression format.
        joblib.dump(artifact, buffer, compress=3)
        return buffer.getvalue()

    @staticmethod
    def _deserialize(payload: bytes) -> Any:
        return joblib.load(BytesIO(payload))

    def save(self, version: str, artifact: Any) -> None:
        payload = self._serialize(artifact)
        path = f"{version}.joblib"
        self.client.storage.from_(self.bucket_name).upload(
            path,
            payload,
            {"upsert": "true", "content-type": "application/octet-stream"},
        )

    def load(self, version: str) -> Any:
        path = f"{version}.joblib"
        payload = self.client.storage.from_(self.bucket_name).download(path)
        return self._deserialize(payload)
