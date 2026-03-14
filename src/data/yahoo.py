"""
Yahoo Finance data source via yfinance.
Handles MNQ=F, NQ=F, MES=F, ES=F and interval limits.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import pandas as pd
import yfinance as yf

from src.constants import OHLCV_CLOSE, OHLCV_HIGH, OHLCV_LOW, OHLCV_OPEN, OHLCV_VOLUME
from src.data.base import BaseDataSource
from src.utils.validation import prepare_ohlcv


# Yahoo interval string
YAHOO_INTERVAL_MAP = {
    "1m": "1m",
    "2m": "2m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "60m": "1h",
}


class YahooDataSource(BaseDataSource):
    """yfinance-based source. Subject to Yahoo intraday lookback limits (e.g. 7d for 1m)."""

    @property
    def name(self) -> str:
        return "yahoo"

    def fetch(
        self,
        symbol: str,
        interval: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        lookback_days: Optional[int] = None,
    ) -> pd.DataFrame:
        if start is None and end is None and lookback_days is None:
            lookback_days = 60
        if end is None:
            end = datetime.now(timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        if start is None and lookback_days is not None:
            start = end - timedelta(days=lookback_days)
        if start is None:
            start = end - timedelta(days=60)
        if start is not None and start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)

        yf_interval = YAHOO_INTERVAL_MAP.get(interval, "5m")
        # Yahoo 1m/2m have short lookback; cap start
        if yf_interval in ("1m", "2m"):
            max_lookback = timedelta(days=7)
            if start < end - max_lookback:
                start = end - max_lookback

        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start, end=end, interval=yf_interval, auto_adjust=True)
        if df.empty or len(df) < 2:
            return pd.DataFrame()

        df = df.rename(columns={
            "Open": OHLCV_OPEN,
            "High": OHLCV_HIGH,
            "Low": OHLCV_LOW,
            "Close": OHLCV_CLOSE,
            "Volume": OHLCV_VOLUME,
        })
        for c in [OHLCV_OPEN, OHLCV_HIGH, OHLCV_LOW, OHLCV_CLOSE]:
            if c not in df.columns:
                return pd.DataFrame()
        if OHLCV_VOLUME not in df.columns:
            df[OHLCV_VOLUME] = 0
        df = df[[OHLCV_OPEN, OHLCV_HIGH, OHLCV_LOW, OHLCV_CLOSE, OHLCV_VOLUME]]
        df.index = pd.to_datetime(df.index)
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC", ambiguous="infer")
        else:
            df.index = df.index.tz_convert("UTC")
        return prepare_ohlcv(df, normalize=False, validate=True, dedupe=True)
