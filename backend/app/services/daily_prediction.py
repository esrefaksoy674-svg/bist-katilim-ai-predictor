from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.services.model_registry import ModelRegistry
from app.services.prediction_repository import PredictionRepository
from app.services.prediction_scan import run_prediction_scan
from app.services.universe import fetch_katilim_universe


@dataclass(frozen=True)
class DailyPredictionRun:
    prediction_date: date
    model_version: str
    universe_count: int
    predictions: list


def run_daily_prediction(
    prediction_date: date,
    registry: ModelRegistry,
    history,
    prediction_repository: PredictionRepository | None = None,
    symbols: list[str] | None = None,
    top_n: int = 10,
    target_date: date | None = None,
) -> DailyPredictionRun:
    """
    Günlük tahmin akışını tek noktadan çalıştırır.

    Evren verilmezse güncel Katılım evreni kaynaktan alınır.
    Yalnızca ACTIVE model kullanılabilir; SHADOW modelle tahmin yapılmaz.
    target_date verilmezse değerlendirme tarihi ayrıca çözümlenmek üzere
    prediction_date kullanılır; gelecekteki piyasa verisi taranmaz.
    """
    active = registry.active()
    if active is None:
        raise RuntimeError("Aktif model bulunamadı.")

    if active.artifact is None:
        raise RuntimeError(
            f"Aktif model artefaktı yüklenmemiş: {active.version}"
        )

    universe = symbols if symbols is not None else fetch_katilim_universe()
    if not universe:
        raise RuntimeError("Tahmin için Katılım evreni boş.")

    predictions = run_prediction_scan(
        symbols=universe,
        prediction_date=prediction_date,
        trained_model=active.artifact,
        model_version=active.version,
        history=history,
        prediction_repository=prediction_repository,
        top_n=top_n,
        target_date=target_date,
    )

    return DailyPredictionRun(
        prediction_date=prediction_date,
        model_version=active.version,
        universe_count=len(set(universe)),
        predictions=predictions,
    )
