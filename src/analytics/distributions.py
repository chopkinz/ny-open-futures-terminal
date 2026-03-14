"""
Distribution analytics: OR width, R, MAE/MFE, weekday, month.
"""
from __future__ import annotations

from collections import defaultdict
from typing import List

from src.models import TradeRecord


def or_width_distribution(trades: List[TradeRecord]) -> List[float]:
    """List of OR widths for trades that have it."""
    return [t.or_width for t in trades if t.or_width is not None]


def r_distribution(trades: List[TradeRecord]) -> List[float]:
    return [t.r_multiple for t in trades if t.r_multiple is not None]


def weekday_breakdown(trades: List[TradeRecord]) -> dict[str, List[TradeRecord]]:
    """Group trades by weekday name."""
    from datetime import datetime
    out = defaultdict(list)
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    for t in trades:
        try:
            dt = datetime.fromisoformat(t.trade_date)
            out[days[dt.weekday()]].append(t)
        except Exception:
            continue
    return dict(out)
