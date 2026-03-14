"""
Timezone and session time utilities.
All session logic uses America/New_York; DST handled by zoneinfo/pytz.
User-facing times: 12-hour AM/PM in display timezone (local or chosen).
"""
from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta
from typing import Optional

import pandas as pd
import pytz

from src.constants import DEFAULT_TZ

NY = pytz.timezone(DEFAULT_TZ)
UTC = pytz.UTC


def get_local_tz():
    """Server's local timezone (user's when running locally)."""
    return datetime.now().astimezone().tzinfo


def parse_time_to_24h(s: str) -> str:
    """
    Parse time string to 24h 'HH:MM'. Accepts:
    - 9:30 AM, 9:30 am, 09:30 AM
    - 12:00 PM, 12:00 pm
    - 09:30, 9:30 (interpreted as 24h if < 12, else treat as hour)
    """
    if not s or not s.strip():
        return "09:30"
    s = s.strip().upper()
    # Try "9:30 AM" or "9:30 PM"
    am_pm = None
    if " AM" in s:
        s = s.replace(" AM", "").strip()
        am_pm = "AM"
    elif " PM" in s:
        s = s.replace(" PM", "").strip()
        am_pm = "PM"
    parts = re.split(r"[\s:]+", s)
    if not parts:
        return "09:30"
    h = int(parts[0])
    m = int(parts[1]) if len(parts) > 1 else 0
    m = min(59, max(0, m))
    if am_pm == "PM" and h != 12:
        h += 12
    elif am_pm == "AM" and h == 12:
        h = 0
    elif am_pm is None and h <= 12 and (len(parts) == 1 or "AM" not in s and "PM" not in s):
        # Assume AM for 1-12
        if h == 12:
            h = 12  # noon
        # else keep as-is for 24h (e.g. 14:30)
        pass
    h = min(23, max(0, h))
    return f"{h:02d}:{m:02d}"


def format_time_12h(hhmm_24: str) -> str:
    """Convert 24h 'HH:MM' to 12h with AM/PM, e.g. '09:30' -> '9:30 AM'."""
    if not hhmm_24 or ":" not in hhmm_24:
        return hhmm_24 or "9:30 AM"
    parts = hhmm_24.strip().split(":")
    h = int(parts[0])
    m = int(parts[1]) if len(parts) > 1 else 0
    if h == 0:
        return f"12:{m:02d} AM"
    if h == 12:
        return f"12:{m:02d} PM"
    if h < 12:
        return f"{h}:{m:02d} AM"
    return f"{h - 12}:{m:02d} PM"


def format_timestamp_12h(ts, display_tz) -> str:
    """Format a timestamp in display_tz as 'Mon, Jan 15, 2025 09:30 AM'."""
    if ts is None:
        return "—"
    if display_tz is None:
        display_tz = UTC
    if hasattr(ts, "tz_localize"):
        if ts.tzinfo is None:
            ts = ts.tz_localize(UTC)
        ts = ts.tz_convert(display_tz)
    elif hasattr(ts, "astimezone"):
        ts = ensure_tz(ts, UTC)
        if display_tz is not UTC:
            ts = ts.astimezone(display_tz)
    else:
        return str(ts)[:19]
    # strftime: %a = weekday abbrev, %b = month abbrev, %d, %Y, %I = 12h, %M, %p = AM/PM
    try:
        return ts.strftime("%a, %b %d, %Y %I:%M %p")
    except Exception:
        return str(ts)[:19]


def get_ny_tz():
    return NY


def ensure_tz(ts: datetime, tz=pytz.UTC) -> datetime:
    """Ensure datetime has timezone; if naive, assume UTC."""
    if ts.tzinfo is None:
        return pytz.UTC.localize(ts)
    return ts.astimezone(tz)


def to_ny_tz(ts: datetime) -> datetime:
    """Convert any datetime to America/New_York."""
    ts = ensure_tz(ts, UTC)
    return ts.astimezone(NY)


def parse_time_today(time_str: str, tz=NY) -> datetime:
    """Parse 'HH:MM' or 'HH:MM:SS' as today in given tz."""
    parts = time_str.strip().split(":")
    h = int(parts[0])
    m = int(parts[1]) if len(parts) > 1 else 0
    s = int(parts[2]) if len(parts) > 2 else 0
    t = time(h, m, s)
    dt = datetime.combine(date.today(), t)
    if dt.tzinfo is None:
        dt = tz.localize(dt)
    return dt


def ny_date_from_utc(utc_ts: datetime) -> date:
    """Get New York trading date for a UTC timestamp (4am NY = new day)."""
    ny_ts = to_ny_tz(ensure_tz(utc_ts, UTC))
    return ny_ts.date()


def trading_day_label(d: date) -> str:
    """Return YYYY-MM-DD for a date."""
    return d.isoformat()


def session_date_from_index(index: pd.DatetimeIndex, tz=NY) -> pd.Series:
    """For each timestamp in index, return the NY session date (before 04:00 NY = previous day)."""
    index = pd.to_datetime(index)
    if index.tz is None:
        index = index.tz_localize(UTC)
    ny = index.tz_convert(NY)
    hour = ny.hour
    session_dates = pd.Series(ny.date, index=index)
    prev_ny = ny - pd.Timedelta(days=1)
    prev_dates = pd.Series(prev_ny.date, index=index)
    session_dates.loc[hour < 4] = prev_dates.loc[hour < 4]
    return session_dates


def _session_tz(tz: Optional[str] = None):
    """Return pytz timezone for session; default NY."""
    if tz is None or tz == "":
        return NY
    if hasattr(tz, "localize"):
        return tz
    return pytz.timezone(tz)


def parse_or_window(or_start: str, or_end: str, session_d: date, tz: Optional[str] = None) -> tuple[datetime, datetime]:
    """Return (start_ts, end_ts) for the opening range on session_d in the given session timezone."""
    session_tz = _session_tz(tz)
    start_parts = or_start.strip().split(":")
    end_parts = or_end.strip().split(":")
    t0 = time(int(start_parts[0]), int(start_parts[1]) if len(start_parts) > 1 else 0)
    t1 = time(int(end_parts[0]), int(end_parts[1]) if len(end_parts) > 1 else 0)
    dt0 = session_tz.localize(datetime.combine(session_d, t0))
    dt1 = session_tz.localize(datetime.combine(session_d, t1))
    return dt0, dt1


def trade_window_end_ts(session_d: date, end_time_str: str, tz: Optional[str] = None) -> datetime:
    """End of trade window on session_d in the given session timezone."""
    session_tz = _session_tz(tz)
    parts = end_time_str.strip().split(":")
    t = time(int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)
    return session_tz.localize(datetime.combine(session_d, t))


def is_weekday(d: date) -> bool:
    """True if Monday–Friday."""
    return d.weekday() < 5


def filter_weekdays(dates: list[date]) -> list[date]:
    return [d for d in dates if is_weekday(d)]
