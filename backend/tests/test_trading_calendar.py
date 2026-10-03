from datetime import date

from app.services.trading_calendar import next_trading_day


def test_next_trading_day_skips_weekend():
    assert next_trading_day(date(2026, 10, 2)) == date(2026, 10, 5)


def test_next_trading_day_skips_national_holiday():
    assert next_trading_day(date(2026, 10, 28)) == date(2026, 10, 30)
