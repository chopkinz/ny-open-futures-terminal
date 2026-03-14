"""
Abstract base for data sources.

The data layer is designed to be swappable: implement BaseDataSource
for any provider (Yahoo, Databento, broker API, etc.). The loader
(src/data/loaders.py) uses cache-first Parquet storage; swap the
source in get_source() or via config without changing strategy or
backtest code. Suitable for adding live execution or broker APIs later.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

import pandas as pd


class BaseDataSource(ABC):
    """Pluggable data source interface. Swap implementations without changing callers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Source identifier; used in cache keys."""
        pass

    @abstractmethod
    def fetch(
        self,
        symbol: str,
        interval: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        lookback_days: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data. Either (start, end) or lookback_days must be provided.
        Returns DataFrame with DatetimeIndex and columns open, high, low, close, volume.
        """
        pass

    def supported_intervals(self) -> list[str]:
        """Return list of supported interval strings."""
        return ["1m", "2m", "5m", "15m", "30m", "60m"]
