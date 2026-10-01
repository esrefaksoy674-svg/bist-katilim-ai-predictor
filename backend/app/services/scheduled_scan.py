from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.services.daily_scan import run_daily_scan

MARKET_TIMEZONE = ZoneInfo("Europe/Istanbul")


def run_scheduled_scan() -> dict:
    """İşlem günü sonrasında günlük öğrenme/tahmin taramasını başlatır."""
    trading_date = datetime.now(MARKET_TIMEZONE).date()
    result = run_daily_scan(trading_date=trading_date)
    return {
        "status": "ok",
        "trading_date": trading_date.isoformat(),
        "result": result,
    }


if __name__ == "__main__":
    print(run_scheduled_scan())
