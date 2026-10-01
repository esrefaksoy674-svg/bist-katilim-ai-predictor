from __future__ import annotations

from datetime import date

import pandas as pd

from app.services.learning_pipeline import (
    build_learning_event,
    process_learning_event,
)
from app.services.market_data import fetch_daily_data


def scan_symbol_for_learning(
    symbol: str,
    signal_date: date,
    repository=None,
):
    """
    Bir hissenin belirtilen işlem gününde >%5 yükselip yükselmediğini
    kontrol eder. Yalnızca >%5 olan günler öğrenme olayı oluşturur.

    Teknik özellikler, sinyal gününden önceki gerçek işlem gününe
    kadar olan veriyle hesaplanır.
    """

    data = fetch_daily_data(symbol, period="2y")
    day_rows = data[data.index.date == signal_date]

    if day_rows.empty:
        return None

    signal_row = day_rows.iloc[-1]
    signal_close = float(signal_row["Close"])

    previous_rows = data[data.index.date < signal_date]
    if previous_rows.empty:
        return None

    reference_date = previous_rows.index[-1].date()
    reference_close = float(previous_rows.iloc[-1]["Close"])

    if reference_close <= 0:
        return None

    rise_percent = (
        (signal_close - reference_close)
        / reference_close
        * 100
    )

    if rise_percent <= 5.0:
        return None

    technical_data = data[data.index.date <= reference_date].copy()

    event = build_learning_event(
        symbol=symbol,
        signal_date=signal_date,
        signal_close=signal_close,
        technical_data=technical_data,
        technical_data_date=reference_date,
    )

    process_learning_event(event, repository=repository)
    return event


def scan_universe_for_learning(
    symbols: list[str],
    signal_date: date,
    repository=None,
) -> dict:
    """
    Katılım evrenini tek bir işlem günü için tarar.

    Hatalı bir sembol tüm taramayı durdurmaz; hata listesine alınır.
    """

    events = []
    errors = []

    for symbol in sorted(set(symbols)):
        try:
            event = scan_symbol_for_learning(
                symbol=symbol,
                signal_date=signal_date,
                repository=repository,
            )
            if event is not None:
                events.append(event)
        except Exception as exc:
            errors.append({
                "symbol": symbol,
                "error": str(exc),
            })

    return {
        "signal_date": signal_date,
        "scanned": len(set(symbols)),
        "events": len(events),
        "events_data": events,
        "errors": errors,
    }
