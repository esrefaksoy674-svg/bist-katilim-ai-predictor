from __future__ import annotations

from app.services.model_evaluation import evaluate_candidate
from app.services.model_registry import ModelRegistry, RegisteredModel


def promote_if_better(
    registry: ModelRegistry,
    candidate_version: str,
) -> RegisteredModel | None:
    """
    Shadow modeli yalnızca mevcut aktif modelden daha iyi doğrulanmışsa
    aktif eder. Aktif model yoksa yeterli örnekli aday ilk model olabilir.
    """

    candidate = registry.get(candidate_version)
    if candidate is None:
        raise ValueError(f"Aday model bulunamadı: {candidate_version}")

    active = registry.active()

    if active is None:
        if candidate.sample_count <= 0:
            return None
        return registry.activate(candidate_version)

    decision = evaluate_candidate(candidate, active)

    if decision != "ELIGIBLE":
        return None

    return registry.activate(candidate_version)
