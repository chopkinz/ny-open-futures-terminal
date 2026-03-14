"""
Unified loader: cache-first Parquet, then source fetch, with normalization.
Swap data source via DataConfig.source or get_source(); same interface for Yahoo,
Databento, or future broker/live feeds.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import pandas as pd

from src.data.base import BaseDataSource
from src.data.cache import CacheLayer
from src.data.databento import DatabentoDataSource
from src.data.yahoo import YahooDataSource
from src.models import DataConfig, DataSource
from src.utils.validation import prepare_ohlcv


def get_source(config: DataConfig) -> BaseDataSource:
    if config.source == DataSource.DATABENTO:
        return DatabentoDataSource()
    return YahooDataSource()


def load_ohlcv(config: DataConfig) -> pd.DataFrame:
    """
    Load OHLCV: use cache if enabled and not refresh; else fetch from source and cache.
    Returns normalized, validated DataFrame with timezone-aware index.
    """
    cache = CacheLayer(config.cache_dir)
    source = get_source(config)

    end = datetime.now(timezone.utc)
    if config.end_date:
        try:
            end = datetime.fromisoformat(config.end_date.replace("Z", "+00:00"))
            if end.tzinfo is None:
                end = end.replace(tzinfo=timezone.utc)
        except Exception:
            pass
    start = None
    if config.start_date:
        try:
            start = datetime.fromisoformat(config.start_date.replace("Z", "+00:00"))
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
        except Exception:
            pass
    if start is None and config.lookback_days:
        start = end - timedelta(days=config.lookback_days)
    lookback_days = config.lookback_days if start is None else None

    if config.use_cache and not config.refresh_cache:
        df = cache.get(
            source.name,
            config.symbol,
            config.interval,
            start=start,
            end=end,
            lookback_days=lookback_days,
        )
        if df is not None and not df.empty:
            return prepare_ohlcv(df, normalize=True, validate=True, dedupe=True)

    df = source.fetch(
        symbol=config.symbol,
        interval=config.interval,
        start=start,
        end=end,
        lookback_days=lookback_days,
    )
    if df.empty:
        return df

    if config.use_cache:
        cache.set(df, source.name, config.symbol, config.interval, start=start, end=end, lookback_days=lookback_days)

    return prepare_ohlcv(df, normalize=True, validate=True, dedupe=True)
