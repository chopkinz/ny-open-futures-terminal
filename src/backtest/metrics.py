"""
Performance metrics from trade list.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any, Optional

import numpy as np

from src.config import get_contract_specs
from src.models import PerformanceSummary, StrategyConfig, TradeRecord


def _get_tick_value(symbol: str) -> float:
    specs = get_contract_specs()
    for root, s in specs.items():
        if symbol.startswith(root) or root in symbol:
            return float(s.get("tick_value", 0.5))
    return 0.5


def pnl_dollars(tr: TradeRecord) -> float:
    if tr.pnl_points is None:
        return 0.0
    tick_val = _get_tick_value(tr.symbol)
    tick_size = 0.25
    if tick_size and tick_val:
        return tr.pnl_points / tick_size * tick_val
    return 0.0


def compute_performance(
    trades: list[TradeRecord],
    symbol: str = "MNQ=F",
    strategy_config: Optional[StrategyConfig] = None,
) -> PerformanceSummary:
    """Compute aggregate performance from trade list."""
    # Filter to triggered trades with valid exit
    valid = [t for t in trades if t.triggered and t.exit_reason != "no_fill" and t.entry_price is not None and t.exit_price is not None]
    if not valid:
        return PerformanceSummary(
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            breakeven_trades=0,
            win_rate=0.0,
            loss_rate=0.0,
            breakeven_rate=0.0,
            expectancy_r=0.0,
            avg_r=0.0,
            median_r=0.0,
            total_r=0.0,
            gross_profit=0.0,
            gross_loss=0.0,
            profit_factor=0.0,
            avg_hold_seconds=0.0,
            max_drawdown=0.0,
            max_win_streak=0,
            max_loss_streak=0,
            trades=[],
        )

    r_list = [t.r_multiple for t in valid if t.r_multiple is not None]
    wins = [t for t in valid if t.r_multiple is not None and t.r_multiple > 0]
    losses = [t for t in valid if t.r_multiple is not None and t.r_multiple < 0]
    be = [t for t in valid if t.r_multiple is not None and t.r_multiple == 0]
    total = len(valid)
    win_count = len(wins)
    loss_count = len(losses)
    be_count = len(be)

    gross_profit = sum(pnl_dollars(t) for t in wins)
    gross_loss = abs(sum(pnl_dollars(t) for t in losses))
    if gross_loss > 0:
        profit_factor = gross_profit / gross_loss
    else:
        profit_factor = float("inf") if gross_profit > 0 else 0.0

    total_r = sum(r_list) if r_list else 0.0
    avg_r = np.mean(r_list) if r_list else 0.0
    median_r = float(np.median(r_list)) if r_list else 0.0
    expectancy_r = avg_r

    hold_times = [t.holding_seconds for t in valid if t.holding_seconds is not None]
    avg_hold = float(np.mean(hold_times)) if hold_times else 0.0

    # Drawdown from equity curve
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for t in valid:
        equity += pnl_dollars(t)
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)

    # Streaks
    max_win_str = 0
    max_loss_str = 0
    cur_win = 0
    cur_loss = 0
    for t in valid:
        r = t.r_multiple
        if r is None:
            continue
        if r > 0:
            cur_win += 1
            cur_loss = 0
            max_win_str = max(max_win_str, cur_win)
        elif r < 0:
            cur_loss += 1
            cur_win = 0
            max_loss_str = max(max_loss_str, cur_loss)
        else:
            cur_win = cur_loss = 0

    return PerformanceSummary(
        total_trades=total,
        winning_trades=win_count,
        losing_trades=loss_count,
        breakeven_trades=be_count,
        win_rate=win_count / total if total else 0,
        loss_rate=loss_count / total if total else 0,
        breakeven_rate=be_count / total if total else 0,
        expectancy_r=expectancy_r,
        avg_r=avg_r,
        median_r=median_r,
        total_r=total_r,
        gross_profit=gross_profit,
        gross_loss=gross_loss,
        profit_factor=profit_factor,
        avg_hold_seconds=avg_hold,
        max_drawdown=max_dd,
        max_win_streak=max_win_str,
        max_loss_streak=max_loss_str,
        trades=valid,
    )


def _parse_trade_date(trade_date: Optional[str]):
    """Return (date, year, iso_week, month_key) or None."""
    if not trade_date:
        return None
    try:
        d = datetime.strptime(trade_date.strip()[:10], "%Y-%m-%d").date()
        iso = d.isocalendar()
        return (d, iso[0], iso[1], d.strftime("%Y-%m"))
    except Exception:
        return None


def compute_period_breakdown(
    trades: list[TradeRecord],
    symbol: str = "MNQ=F",
) -> dict[str, Any]:
    """
    Break down trades by day, week, and month. Returns:
    - daily: list of {period, period_label, trades, pnl, wins, losses, win_rate}
    - weekly: same
    - monthly: same
    - summary: avg_trades_per_day, avg_pnl_per_day, best_day, worst_day, etc.
    """
    valid = [t for t in trades if t.triggered and t.exit_reason != "no_fill" and t.entry_price is not None and t.exit_price is not None]
    if not valid:
        return {
            "daily": [],
            "weekly": [],
            "monthly": [],
            "summary": {},
        }

    def agg_period(period_key: str, period_label: str, period_trades: list[TradeRecord]):
        pnls = [pnl_dollars(t) for t in period_trades]
        wins = sum(1 for t in period_trades if t.r_multiple is not None and t.r_multiple > 0)
        losses = sum(1 for t in period_trades if t.r_multiple is not None and t.r_multiple < 0)
        n = len(period_trades)
        return {
            "period": period_key,
            "period_label": period_label,
            "trades": n,
            "pnl": sum(pnls),
            "wins": wins,
            "losses": losses,
            "win_rate": wins / n if n else 0,
        }

    by_day: dict[str, list[TradeRecord]] = defaultdict(list)
    by_week: dict[str, list[TradeRecord]] = defaultdict(list)
    by_month: dict[str, list[TradeRecord]] = defaultdict(list)

    for t in valid:
        parsed = _parse_trade_date(t.trade_date)
        if not parsed:
            continue
        d, year, week, month_key = parsed
        day_key = d.strftime("%Y-%m-%d")
        week_key = f"{year}-W{week:02d}"
        by_day[day_key].append(t)
        by_week[week_key].append(t)
        by_month[month_key].append(t)

    daily = [agg_period(k, k, by_day[k]) for k in sorted(by_day.keys())]
    weekly = [agg_period(k, k, by_week[k]) for k in sorted(by_week.keys())]
    monthly = [agg_period(k, k, by_month[k]) for k in sorted(by_month.keys())]

    # Summary stats
    summary = {}
    if daily:
        trades_per_day = [x["trades"] for x in daily]
        pnl_per_day = [x["pnl"] for x in daily]
        summary["avg_trades_per_day"] = float(np.mean(trades_per_day))
        summary["avg_pnl_per_day"] = float(np.mean(pnl_per_day))
        summary["total_days_with_trades"] = len(daily)
        best = max(daily, key=lambda x: x["pnl"])
        worst = min(daily, key=lambda x: x["pnl"])
        summary["best_day"] = (best["period"], best["pnl"])
        summary["worst_day"] = (worst["period"], worst["pnl"])
    if weekly:
        summary["avg_trades_per_week"] = float(np.mean([x["trades"] for x in weekly]))
        summary["avg_pnl_per_week"] = float(np.mean([x["pnl"] for x in weekly]))
        summary["total_weeks_with_trades"] = len(weekly)
    if monthly:
        summary["avg_trades_per_month"] = float(np.mean([x["trades"] for x in monthly]))
        summary["avg_pnl_per_month"] = float(np.mean([x["pnl"] for x in monthly]))
        summary["total_months_with_trades"] = len(monthly)

    return {
        "daily": daily,
        "weekly": weekly,
        "monthly": monthly,
        "summary": summary,
    }
