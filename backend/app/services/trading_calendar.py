from __future__ import annotations

from datetime import date, timedelta

import exchange_calendars as exchange_calendars
import pandas as pd


CALENDAR_NAME = "XIST"
SEARCH_WINDOW_DAYS = 14


def _calendar_sessions(start_date: date, end_date: date):
    calendar = exchange_calendars.get_calendar(
        CALENDAR_NAME,
        start=pd.Timestamp(start_date),
        end=pd.Timestamp(end_date),
    )
    return calendar.sessions_in_range(
        calendar.first_session,
        calendar.last_session,
    )


def next_trading_day(trading_date: date) -> date:
    """Return the next scheduled Istanbul Stock Exchange session."""
    end_date = trading_date + timedelta(days=SEARCH_WINDOW_DAYS)
    sessions = _calendar_sessions(trading_date, end_date)
    next_sessions = sessions[sessions.date > trading_date]
    if next_sessions.empty:
        raise RuntimeError(
            f"XIST takviminde {trading_date} sonrasında işlem günü bulunamadı."
        )
    return next_sessions[0].date()


def latest_trading_day(on_or_before: date) -> date:
    """Return the latest scheduled session on or before a calendar date."""
    start_date = on_or_before - timedelta(days=SEARCH_WINDOW_DAYS)
    sessions = _calendar_sessions(start_date, on_or_before)
    eligible_sessions = sessions[sessions.date <= on_or_before]
    if eligible_sessions.empty:
        raise RuntimeError(
            f"XIST takviminde {on_or_before} tarihinde veya öncesinde "
            "işlem günü bulunamadı."
        )
    return eligible_sessions[-1].date()
