"""
Session engine: slice data by NY session, compute session dates, filter weekdays.
"""
from __future__ import annotations

from datetime import date, datetime, time
from typing import Optional

import pandas as pd  # pyright: ignore[reportMissingImports]
import pytz  # pyright: ignore[reportMissingModuleSource]

from src.models import SessionConfig
from src.utils.time import (
    filter_weekdays,
    is_weekday,
    ny_date_from_utc,
    parse_or_window,
    to_ny_tz,
    trade_window_end_ts,
)

NY = pytz.timezone("America/New_York")
UTC = pytz.UTC


def _session_tz(config: SessionConfig):
    """Pytz timezone for session (e.g. America/Chicago for CST)."""
    return pytz.timezone(config.timezone)


class SessionEngine:
    """Session and opening-range logic in session timezone (e.g. CST)."""

    def __init__(self, config: Optional[SessionConfig] = None):
        self.config = config or SessionConfig()

    def session_dates_from_index(self, index: pd.DatetimeIndex) -> pd.Series:
        """Return session date for each timestamp (date in session timezone, e.g. CST)."""
        index = pd.to_datetime(index)
        if index.tz is None:
            index = index.tz_localize(UTC)
        tz = _session_tz(self.config)
        local = index.tz_convert(tz)
        # Session date: before 04:00 local = previous calendar day
        hour = local.hour
        session_dates = pd.Series(local.date, index=index)
        prev_local = local - pd.Timedelta(days=1)
        prev_dates = pd.Series(prev_local.date, index=index)
        session_dates.loc[hour < 4] = prev_dates.loc[hour < 4]
        return session_dates

    def unique_session_dates(self, df: pd.DataFrame) -> list[date]:
        """Unique NY session dates in the data, weekdays only."""
        if df.empty:
            return []
        ser = self.session_dates_from_index(df.index)
        uniq = ser.dropna().unique()
        def _to_py_date(x):
            if hasattr(x, "date") and callable(getattr(x, "date")):
                return x.date()
            return x
        dates_normalized = [_to_py_date(d) for d in uniq]
        return filter_weekdays(sorted(set(d for d in dates_normalized if isinstance(d, date))))

    def get_or_bounds(self, session_d: date) -> tuple[datetime, datetime]:
        """Opening range (start_ts, end_ts) in session timezone for session_d."""
        return parse_or_window(
            self.config.or_start,
            self.config.or_end,
            session_d,
            self.config.timezone,
        )

    def get_trade_window_end(self, session_d: date) -> datetime:
        """End of trade window for session_d."""
        return trade_window_end_ts(session_d, self.config.trade_window_end, self.config.timezone)

    def slice_session(
        self,
        df: pd.DataFrame,
        session_d: date,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> pd.DataFrame:
        """Return rows that fall on session_d between start_time and end_time (HH:MM in session tz)."""
        if df.empty:
            return df
        ser = self.session_dates_from_index(df.index)

        def _to_date(x):
            if hasattr(x, "date") and callable(getattr(x, "date")):
                return x.date()
            return x

        mask = ser.apply(_to_date) == session_d
        sub = df.loc[mask]
        if sub.empty:
            return sub
        if sub.index.tz is not None:
            df_tz = sub.index.tz
        else:
            df_tz = UTC
        session_tz = _session_tz(self.config)
        if start_time:
            parts = start_time.split(":")
            h, m = int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
            t0_local = session_tz.localize(datetime.combine(session_d, time(h, m)))
            t0 = t0_local.astimezone(df_tz)
            sub = sub.loc[sub.index >= t0]
        if end_time:
            parts = end_time.split(":")
            h, m = int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
            t1_local = session_tz.localize(datetime.combine(session_d, time(h, m)))
            t1 = t1_local.astimezone(df_tz)
            sub = sub.loc[sub.index <= t1]
        return sub


def get_session_dates(df: pd.DataFrame, config: Optional[SessionConfig] = None) -> list[date]:
    """Convenience: unique weekday session dates in df."""
    engine = SessionEngine(config)
    return engine.unique_session_dates(df)
