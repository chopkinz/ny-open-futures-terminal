"""
Base strategy interface.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd
    from src.models import OpeningRange, SessionConfig, StrategyConfig


class BaseStrategy(ABC):
    """Strategy produces trade ideas; backtest engine runs execution."""

    @abstractmethod
    def run(
        self,
        df: pd.DataFrame,
        or_map: dict[str, OpeningRange],
        session_config: SessionConfig,
        strategy_config: StrategyConfig,
    ) -> list:
        """Return list of TradeRecord (or raw signals for engine to fill)."""
        pass
