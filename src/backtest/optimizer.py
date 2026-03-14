"""
Optimize SL/TP (target R) over historical data. Grid search to find best R multiple.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd

from src.backtest.engine import run_backtest
from src.models import DataConfig, PerformanceSummary, SessionConfig, StrategyConfig, TradeRecord


@dataclass
class OptimizationResult:
    """Best R and performance from grid search."""
    best_r: float
    best_perf: PerformanceSummary
    best_trades: list[TradeRecord]
    all_results: list[tuple[float, PerformanceSummary]]


def optimize_r(
    df: pd.DataFrame,
    data_config: DataConfig,
    session_config: SessionConfig,
    strategy_config: StrategyConfig,
    r_min: float = 0.5,
    r_max: float = 3.0,
    r_step: float = 0.25,
    metric: str = "expectancy_r",
) -> Optional[OptimizationResult]:
    """
    Grid search over R multiples. Keeps stop = opposite OR side, target = fixed R.
    Returns best R and corresponding trades/perf, or None if no valid runs.
    """
    if df.empty:
        return None

    r_values = []
    r = r_min
    while r <= r_max:
        r_values.append(round(r, 2))
        r += r_step

    best_perf: Optional[PerformanceSummary] = None
    best_trades: list[TradeRecord] = []
    best_r: Optional[float] = None
    all_results: list[tuple[float, PerformanceSummary]] = []

    for r_val in r_values:
        config = strategy_config.model_copy(update={"r_multiple": r_val})
        trades, perf = run_backtest(df, data_config, session_config, config)
        all_results.append((r_val, perf))

        # Require at least 2 trades so we can pick best R even with a few days of data
        if perf.total_trades < 2:
            continue

        if metric == "expectancy_r":
            score = perf.expectancy_r
        elif metric == "total_r":
            score = perf.total_r
        elif metric == "profit_factor":
            score = perf.profit_factor if perf.profit_factor != float("inf") else 0.0
        elif metric == "win_rate":
            score = perf.win_rate  # higher = better; we want closest to 100%
        else:
            score = perf.expectancy_r

        if best_perf is None:
            best_score = score
        elif metric == "expectancy_r":
            best_score = best_perf.expectancy_r
        elif metric == "total_r":
            best_score = best_perf.total_r
        elif metric == "win_rate":
            best_score = best_perf.win_rate
        else:
            best_score = best_perf.profit_factor if best_perf.profit_factor != float("inf") else 0.0

        if best_perf is None or score > best_score:
            best_perf = perf
            best_trades = trades
            best_r = r_val

    if best_perf is None or best_r is None:
        return None
    return OptimizationResult(best_r=best_r, best_perf=best_perf, best_trades=best_trades, all_results=all_results)
