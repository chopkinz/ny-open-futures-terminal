"""
Opening range and session structure analytics.
"""
from __future__ import annotations

import pandas as pd

from src.constants import OHLCV_HIGH, OHLCV_LOW, OHLCV_VOLUME
from src.models import OpeningRange
from src.sessions.engine import SessionEngine


def compute_opening_ranges(
    df: pd.DataFrame,
    session_engine: SessionEngine,
) -> dict[str, OpeningRange]:
    """
    Compute opening range for each session date in df.
    Returns dict keyed by date string YYYY-MM-DD.
    """
    if df.empty:
        return {}
    dates = session_engine.unique_session_dates(df)
    out = {}
    for d in dates:
        or_start_ts, or_end_ts = session_engine.get_or_bounds(d)
        # Slice bars in [or_start_ts, or_end_ts]; use bounds in df's tz for comparison only
        if df.index.tz is None:
            mask_start = or_start_ts.replace(tzinfo=None)
            mask_end = or_end_ts.replace(tzinfo=None)
        else:
            mask_start = or_start_ts.astimezone(df.index.tz)
            mask_end = or_end_ts.astimezone(df.index.tz)
        mask = (df.index >= mask_start) & (df.index <= mask_end)
        bars = df.loc[mask]
        if bars.empty:
            continue
        or_high = bars[OHLCV_HIGH].max()
        or_low = bars[OHLCV_LOW].min()
        or_mid = (or_high + or_low) / 2
        or_width = or_high - or_low
        or_volume = float(bars[OHLCV_VOLUME].sum()) if OHLCV_VOLUME in bars.columns else 0.0
        date_str = d.isoformat()
        # Store original NY-aware bounds so execution can convert as needed
        out[date_str] = OpeningRange(
            date=date_str,
            or_high=float(or_high),
            or_low=float(or_low),
            or_mid=float(or_mid),
            or_width=float(or_width),
            or_start_ts=or_start_ts,
            or_end_ts=or_end_ts,
            bar_count=len(bars),
            or_volume=or_volume,
        )
    return out
