from datetime import date

from app.services.trading_calendar import latest_trading_day, next_trading_day


def test_next_trading_day_skips_weekend():
    assert next_trading_day(date(2026, 10, 2)) == date(2026, 10, 5)


def test_next_trading_day_skips_national_holiday():
    assert next_trading_day(date(2026, 10, 28)) == date(2026, 10, 30)


def test_latest_trading_day_on_weekend():
    assert latest_trading_day(date(2026, 10, 3)) == date(2026, 10, 2)


def test_latest_trading_day_on_session():
    assert latest_trading_day(date(2026, 10, 5)) == date(2026, 10, 5)
