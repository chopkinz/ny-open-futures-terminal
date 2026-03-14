"""
Opening Range Breakout strategy: detect first break of OR high/low, simulate trade.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    import pandas as pd
    from src.models import OpeningRange, SessionConfig, StrategyConfig

from src.constants import OHLCV_CLOSE, OHLCV_HIGH, OHLCV_LOW, SETUP_ORB
from src.models import TradeRecord
from src.strategies.base import BaseStrategy


class ORBStrategy(BaseStrategy):
    """ORB: first breakout of opening range after OR end."""

    def run(
        self,
        df: pd.DataFrame,
        or_map: dict[str, OpeningRange],
        session_config: SessionConfig,
        strategy_config: StrategyConfig,
    ) -> list[TradeRecord]:
        """Produce trade records; execution (fill, stop, target) is in backtest engine."""
        from src.backtest.execution import run_day_orb
        from src.sessions.engine import SessionEngine

        engine = SessionEngine(session_config)
        dates = engine.unique_session_dates(df)
        trades = []
        for d in dates:
            date_str = d.isoformat()
            if date_str not in or_map:
                continue
            day_trades = run_day_orb(
                df=df,
                session_d=d,
                or_=or_map[date_str],
                session_config=session_config,
                strategy_config=strategy_config,
            )
            if strategy_config.one_trade_per_day and day_trades:
                trades.append(day_trades[0])
            else:
                trades.extend(day_trades)
        return trades
