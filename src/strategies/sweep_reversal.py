"""
Sweep + Reversal strategy: first liquidity sweep of OR side then expansion opposite.
Phase 2: full implementation.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd
    from src.models import OpeningRange, SessionConfig, StrategyConfig

from src.models import TradeRecord
from src.strategies.base import BaseStrategy


class SweepReversalStrategy(BaseStrategy):
    """Detect sweep then reversal; evaluate follow-through."""

    def run(
        self,
        df: pd.DataFrame,
        or_map: dict[str, OpeningRange],
        session_config: SessionConfig,
        strategy_config: StrategyConfig,
    ) -> list[TradeRecord]:
        # Placeholder: return empty list until Phase 2 logic is implemented.
        return []
