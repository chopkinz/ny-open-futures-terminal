"""
Pattern analysis from backtest trades: entry time distribution, typical windows,
and highest win-rate / profit-potential patterns.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.models import TradeRecord


@dataclass
class EntryTimePattern:
    """Summary of when entries typically occur."""
    entry_minutes_since_midnight: list[float]  # for percentile calc
    typical_start_minutes: float   # e.g. 9*60+35 = 575
    typical_end_minutes: float     # e.g. 9*60+50 = 590
    median_entry_minutes: float
    trade_count: int


def _entry_to_minutes(ts: Optional[datetime]) -> Optional[float]:
    """Minutes since midnight (NY) for entry timestamp."""
    if ts is None or not hasattr(ts, "hour"):
        return None
    return ts.hour * 60.0 + ts.minute + ts.second / 60.0


def compute_entry_time_pattern(trades: list[TradeRecord]) -> Optional[EntryTimePattern]:
    """
    From historical trades, compute when entries typically occur.
    Returns 25th–75th percentile window as "typical" entry window.
    """
    minutes_list = []
    for t in trades:
        if not t.triggered or t.entry_ts is None:
            continue
        m = _entry_to_minutes(t.entry_ts)
        if m is not None:
            minutes_list.append(m)
    if len(minutes_list) < 3:
        return None
    minutes_list.sort()
    n = len(minutes_list)
    p25 = minutes_list[int(0.25 * n)]
    p75 = minutes_list[int(0.75 * n)]
    median = minutes_list[n // 2]
    return EntryTimePattern(
        entry_minutes_since_midnight=minutes_list,
        typical_start_minutes=p25,
        typical_end_minutes=p75,
        median_entry_minutes=median,
        trade_count=n,
    )


def format_entry_window(minutes: float) -> str:
    """Convert minutes-since-midnight to 12h string like '9:35 AM'."""
    h = int(minutes // 60)
    m = int(minutes % 60)
    if h == 0:
        return f"12:{m:02d} AM"
    if h < 12:
        return f"{h}:{m:02d} AM"
    if h == 12:
        return f"12:{m:02d} PM"
    return f"{h - 12}:{m:02d} PM"


@dataclass
class BestPattern:
    """A pattern bucket: direction, win rate, avg R, trade count, optional time window."""
    direction: str
    win_rate: float
    avg_r: float
    count: int
    time_start_minutes: Optional[float] = None
    time_end_minutes: Optional[float] = None


def compute_best_patterns(trades: list[TradeRecord]) -> list[BestPattern]:
    """
    Find patterns with the highest win rate and profit potential.
    Returns by direction (long/short) and optionally by 15-min entry-time buckets.
    """
    valid = [t for t in trades if t.triggered and t.r_multiple is not None]
    if len(valid) < 5:
        return []

    results: list[BestPattern] = []

    # By direction
    for direction in ("long", "short"):
        subset = [t for t in valid if t.direction == direction]
        if len(subset) < 2:
            continue
        wins = sum(1 for t in subset if t.r_multiple and t.r_multiple > 0)
        win_rate = wins / len(subset)
        avg_r = sum(t.r_multiple for t in subset if t.r_multiple is not None) / len(subset)
        results.append(BestPattern(direction=direction, win_rate=win_rate, avg_r=avg_r, count=len(subset)))

    # By 15-min entry bucket (e.g. 9:30-9:45, 9:45-10:00) to find best time window
    bucket_size = 15.0
    by_bucket: dict[tuple[str, int], list[TradeRecord]] = {}
    for t in valid:
        if t.entry_ts is None:
            continue
        m = _entry_to_minutes(t.entry_ts)
        if m is None:
            continue
        bucket_idx = int(m // bucket_size) * int(bucket_size)
        key = (t.direction, bucket_idx)
        by_bucket.setdefault(key, []).append(t)
    for (direction, bucket_start), subset in by_bucket.items():
        if len(subset) < 2:
            continue
        wins = sum(1 for t in subset if t.r_multiple and t.r_multiple > 0)
        win_rate = wins / len(subset)
        avg_r = sum(t.r_multiple for t in subset if t.r_multiple is not None) / len(subset)
        bucket_end = bucket_start + bucket_size
        results.append(
            BestPattern(
                direction=direction,
                win_rate=win_rate,
                avg_r=avg_r,
                count=len(subset),
                time_start_minutes=float(bucket_start),
                time_end_minutes=bucket_end,
            )
        )

    # Sort by win rate descending, then by avg R
    results.sort(key=lambda p: (p.win_rate, p.avg_r), reverse=True)
    return results
