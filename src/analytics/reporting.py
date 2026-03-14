"""
Reporting helpers for export and summaries.
"""
from __future__ import annotations

import csv
import io
from typing import List

from src.models import TradeRecord


def trades_to_csv(trades: List[TradeRecord]) -> str:
    """Export trade list to CSV string."""
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow([
        "trade_date", "symbol", "setup_type", "direction", "entry_ts", "entry_price",
        "stop_price", "target_price", "exit_ts", "exit_price", "exit_reason",
        "mae", "mfe", "r_multiple", "pnl_points", "holding_seconds", "or_high", "or_low", "or_width",
    ])
    for t in trades:
        w.writerow([
            t.trade_date, t.symbol, t.setup_type, t.direction,
            t.entry_ts, t.entry_price, t.stop_price, t.target_price,
            t.exit_ts, t.exit_price, t.exit_reason,
            t.mae, t.mfe, t.r_multiple, t.pnl_points, t.holding_seconds,
            t.or_high, t.or_low, t.or_width,
        ])
    return out.getvalue()
