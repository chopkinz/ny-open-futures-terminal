"""
Backtest runner: load data, compute ORs, run strategy, aggregate metrics.
"""
from __future__ import annotations

from typing import Optional

import pandas as pd

from src.analytics.structure import compute_opening_ranges
from src.backtest.metrics import compute_performance
from src.models import DataConfig, PerformanceSummary, SessionConfig, StrategyConfig, StrategyMode, TradeRecord
from src.sessions.engine import SessionEngine
from src.strategies.failed_breakout import FailedBreakoutStrategy
from src.strategies.opening_range_breakout import ORBStrategy
from src.strategies.sweep_reversal import SweepReversalStrategy


def run_backtest(
    df: pd.DataFrame,
    data_config: DataConfig,
    session_config: SessionConfig,
    strategy_config: StrategyConfig,
    symbol: Optional[str] = None,
) -> tuple[list[TradeRecord], PerformanceSummary]:
    """
    Run backtest: compute ORs, run strategy, compute performance.
    Returns (trades, performance_summary).
    """
    if df.empty:
        return [], compute_performance([], symbol or data_config.symbol)

    engine = SessionEngine(session_config)
    or_map = compute_opening_ranges(df, engine)
    if not or_map:
        return [], compute_performance([], symbol or data_config.symbol)

    if strategy_config.mode == StrategyMode.FAILED_BREAKOUT:
        strategy = FailedBreakoutStrategy()
    elif strategy_config.mode == StrategyMode.SWEEP_REVERSAL:
        strategy = SweepReversalStrategy()
    else:
        strategy = ORBStrategy()

    trades = strategy.run(df, or_map, session_config, strategy_config)
    sym = symbol or data_config.symbol
    perf = compute_performance(trades, sym, strategy_config)
    return trades, perf
