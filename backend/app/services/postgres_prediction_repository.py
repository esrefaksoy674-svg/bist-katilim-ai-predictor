from __future__ import annotations

import json
import os
from datetime import date, datetime
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import psycopg
from psycopg.rows import dict_row

from app.models.prediction import Prediction


class PostgresPredictionRepository:
    """Isolated Postgres storage for the 2026-10-02 comparison deployment."""

    def __init__(self, database_url: str):
        self.database_url = self._normalize_url(database_url)
        self._ensure_schema()

    @staticmethod
    def _normalize_url(url: str) -> str:
        # Render may provide postgres://; psycopg accepts postgresql://.
        return "postgresql://" + url[len("postgres://"):] if url.startswith("postgres://") else url

    def _connect(self):
        return psycopg.connect(self.database_url, row_factory=dict_row, connect_timeout=10)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    symbol TEXT NOT NULL,
                    prediction_date DATE NOT NULL,
                    target_date DATE NOT NULL,
                    probability_above_5 DOUBLE PRECISION NOT NULL,
                    expected_change_percent DOUBLE PRECISION NOT NULL,
                    model_confidence DOUBLE PRECISION NOT NULL,
                    pattern_count INTEGER NOT NULL DEFAULT 0,
                    explanation JSONB NOT NULL DEFAULT '{}'::jsonb,
                    model_version TEXT NOT NULL,
                    actual_change_percent DOUBLE PRECISION NULL,
                    successful BOOLEAN NULL,
                    evaluated_at TIMESTAMPTZ NULL,
                    created_at TIMESTAMPTZ NOT NULL,
                    PRIMARY KEY (symbol, prediction_date, model_version)
                )
            """)

    @staticmethod
    def _to_row(prediction: Prediction) -> dict[str, Any]:
        return {
            "symbol": prediction.symbol.upper(),
            "prediction_date": prediction.prediction_date,
            "target_date": prediction.target_date,
            "probability_above_5": prediction.probability_above_5,
            "expected_change_percent": prediction.expected_change_percent,
            "model_confidence": prediction.model_confidence,
            "pattern_count": prediction.pattern_count,
            "explanation": json.dumps(prediction.explanation or {}),
            "model_version": prediction.model_version,
            "actual_change_percent": prediction.actual_change_percent,
            "successful": prediction.successful,
            "evaluated_at": prediction.evaluated_at,
            "created_at": prediction.created_at,
        }

    @staticmethod
    def _from_row(row: dict[str, Any]) -> Prediction:
        return Prediction(**row)

    def add(self, prediction: Prediction) -> None:
        row = self._to_row(prediction)
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO predictions (
                    symbol, prediction_date, target_date, probability_above_5,
                    expected_change_percent, model_confidence, pattern_count,
                    explanation, model_version, actual_change_percent,
                    successful, evaluated_at, created_at
                ) VALUES (
                    %(symbol)s, %(prediction_date)s, %(target_date)s, %(probability_above_5)s,
                    %(expected_change_percent)s, %(model_confidence)s, %(pattern_count)s,
                    %(explanation)s::jsonb, %(model_version)s, %(actual_change_percent)s,
                    %(successful)s, %(evaluated_at)s, %(created_at)s
                )
                ON CONFLICT (symbol, prediction_date, model_version) DO UPDATE SET
                    target_date = EXCLUDED.target_date,
                    probability_above_5 = EXCLUDED.probability_above_5,
                    expected_change_percent = EXCLUDED.expected_change_percent,
                    model_confidence = EXCLUDED.model_confidence,
                    pattern_count = EXCLUDED.pattern_count,
                    explanation = EXCLUDED.explanation,
                    actual_change_percent = EXCLUDED.actual_change_percent,
                    successful = EXCLUDED.successful,
                    evaluated_at = EXCLUDED.evaluated_at
            """, row)

    def get_by_date(self, prediction_date: date) -> list[Prediction]:
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT * FROM predictions
                WHERE prediction_date = %s
                ORDER BY probability_above_5 DESC
            """, (prediction_date,)).fetchall()
        return [self._from_row(row) for row in rows]
