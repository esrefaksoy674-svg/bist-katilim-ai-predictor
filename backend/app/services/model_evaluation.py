from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelMetrics:
    accuracy: float
    precision: float
    recall: float
    sample_count: int


def is_better_model(
    candidate: ModelMetrics,
    active: ModelMetrics,
) -> bool:
    """
    Aday modelin aktif modelden daha iyi olup olmadığını
    belirler.

    Öncelik:
    1. Accuracy
    2. Precision
    3. Recall

    Eşitlik durumunda aktif model korunur.
    """

    candidate_score = (
        candidate.accuracy,
        candidate.precision,
        candidate.recall,
    )

    active_score = (
        active.accuracy,
        active.precision,
        active.recall,
    )

    return candidate_score > active_score


def evaluate_candidate(
    candidate: ModelMetrics,
    active: ModelMetrics | None,
) -> str:
    """
    Aday modelin durumunu belirler.

    Aktif model yoksa aday değerlendirmeye alınabilir.
    Daha iyi değilse SHADOW olarak kalır.
    """

    if candidate.sample_count <= 0:
        return "REJECTED"

    if active is None:
        return "ELIGIBLE"

    if is_better_model(
        candidate,
        active,
    ):
        return "ELIGIBLE"

    return "SHADOW"
