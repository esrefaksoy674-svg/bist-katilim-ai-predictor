from __future__ import annotations

from datetime import date

# New learning epoch approved by the user. Raw market candles are intentionally
# retained; only learned examples and prediction evaluation are epoch-scoped.
LEARNING_EPOCH_START = date(2026, 10, 14)
LEARNING_EPOCH_VERSION = "cold-start-2026-10-14-v1"


def is_in_learning_epoch(value: date) -> bool:
    return value >= LEARNING_EPOCH_START
