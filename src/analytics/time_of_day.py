"""
Time-of-day analytics: breakout timing, session high/low timing, expansion by bucket.
"""
from __future__ import annotations

from collections import defaultdict
from typing import List, Optional

from src.models import TradeRecord


def breakout_time_distribution(trades: List[TradeRecord]) -> dict[int, int]:
    """Count trades by entry hour (NY). Returns {hour: count}."""
    out = defaultdict(int)
    for t in trades:
        if t.entry_ts is None:
            continue
        h = t.entry_ts.hour if hasattr(t.entry_ts, "hour") else 0
        out[h] += 1
    return dict(out)


def avg_r_by_hour(trades: List[TradeRecord]) -> dict[int, float]:
    """Average R multiple by entry hour."""
    by_hour = defaultdict(list)
    for t in trades:
        if t.entry_ts is None or t.r_multiple is None:
            continue
        h = t.entry_ts.hour if hasattr(t.entry_ts, "hour") else 0
        by_hour[h].append(t.r_multiple)
    return {h: sum(v) / len(v) if v else 0.0 for h, v in by_hour.items()}
