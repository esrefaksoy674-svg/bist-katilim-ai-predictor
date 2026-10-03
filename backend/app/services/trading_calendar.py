from __future__ import annotations

from datetime import date, timedelta

import exchange_calendars as exchange_calendars
import pandas as pd


CALENDAR_NAME = "XIST"
SEARCH_WINDOW_DAYS = 14


def next_trading_day(trading_date: date) -> date:
    """Return the next scheduled Istanbul Stock Exchange session."""
    start = pd.Timestamp(trading_date + timedelta(days=1))
    end = start + pd.Timedelta(days=SEARCH_WINDOW_DAYS)
    calendar = exchange_calendars.get_calendar(
        CALENDAR_NAME,
        start=start,
        end=end,
    )
    sessions = calendar.sessions_in_range(start, end)
    if sessions.empty:
        raise RuntimeError(
            f"XIST takviminde {trading_date} sonrasında işlem günü bulunamadı."
        )
    return sessions[0].date()
