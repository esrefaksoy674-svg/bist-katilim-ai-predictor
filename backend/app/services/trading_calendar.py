from __future__ import annotations

from datetime import date, timedelta

import exchange_calendars as exchange_calendars
import pandas as pd


CALENDAR_NAME = "XIST"
SEARCH_WINDOW_DAYS = 14


def next_trading_day(trading_date: date) -> date:
    """Return the next scheduled Istanbul Stock Exchange session."""
    start = pd.Timestamp(trading_date)
    end = start + pd.Timedelta(days=SEARCH_WINDOW_DAYS)
    calendar = exchange_calendars.get_calendar(
        CALENDAR_NAME,
        start=start,
        end=end,
    )
    sessions = calendar.sessions_in_range(
        calendar.first_session,
        calendar.last_session,
    )
    next_sessions = sessions[sessions.date > trading_date]
    if next_sessions.empty:
        raise RuntimeError(
            f"XIST takviminde {trading_date} sonrasında işlem günü bulunamadı."
        )
    return next_sessions[0].date()
