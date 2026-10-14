from __future__ import annotations

import numpy as np
import pandas as pd

from app.services.learning_epoch import LEARNING_EPOCH_VERSION
from app.services.model_registry import ModelRegistry
from app.services.model_training import TrainedModel


class FreshStartScorer:
    """Deterministic cold-start scorer; deliberately contains no prior learned model."""

    def predict_proba(self, features):
        frame = pd.DataFrame(features).copy()

        def numeric(name):
            if name not in frame.columns:
                return pd.Series(0.0, index=frame.index)
            return pd.to_numeric(frame[name], errors="coerce").fillna(0.0)

        rsi = numeric("rsi")
        score = (
            ((rsi >= 40) & (rsi <= 68)).astype(float)
            + (numeric("macd_histogram") > 0).astype(float)
            + (numeric("volume_ratio") >= 1.2).astype(float)
            + (numeric("momentum") > 0).astype(float)
            + (numeric("price_vs_vwap_percent") > 0).astype(float)
            + (numeric("price_vs_sma20_percent") > 0).astype(float)
        )
        probability = (0.25 + (score / 6.0) * 0.65).clip(0.01, 0.90)
        positive = probability.to_numpy(dtype=float)
        return np.column_stack((1.0 - positive, positive))


def load_active_model() -> tuple[ModelRegistry, object]:
    """Start a genuinely fresh epoch without loading any pre-reset model artifact.

    Historic OHLCV remains available to calculate current technical indicators.
    Previously trained model artifacts and learned pattern examples are not used.
    """
    from app.services.prediction_engine import FEATURE_NAMES

    artifact = TrainedModel(
        model=FreshStartScorer(),
        feature_names=list(FEATURE_NAMES),
        sample_count=0,
        metrics={"accuracy": 0.0, "cold_start": True},
    )
    registry = ModelRegistry()
    registry.register_shadow(
        version=LEARNING_EPOCH_VERSION,
        sample_count=0,
        pattern_count=0,
        artifact=artifact,
    )
    registry.activate(LEARNING_EPOCH_VERSION)
    return registry, artifact
