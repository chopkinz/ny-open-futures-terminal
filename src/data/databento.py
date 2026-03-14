"""
Databento data source adapter (skeleton).
If API key is provided, historical download can be implemented.
App runs fully on Yahoo when no key is set.
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

import pandas as pd

from src.data.base import BaseDataSource


class DatabentoDataSource(BaseDataSource):
    """Databento historical data. Requires DATABENTO_API_KEY env var."""

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or os.environ.get("DATABENTO_API_KEY")

    @property
    def name(self) -> str:
        return "databento"

    def is_available(self) -> bool:
        return bool(self._api_key)

    def fetch(
        self,
        symbol: str,
        interval: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        lookback_days: Optional[int] = None,
    ) -> pd.DataFrame:
        if not self.is_available():
            return pd.DataFrame()
        # Placeholder: actual implementation would use databento client
        # to request historical bars and return normalized OHLCV DataFrame.
        return pd.DataFrame()
