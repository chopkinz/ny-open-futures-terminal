"""
Local parquet cache for OHLCV data.
Cache key: source / symbol / interval / start / end (or lookback).
"""
from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd


def _cache_key(source: str, symbol: str, interval: str, start: Optional[datetime], end: Optional[datetime], lookback_days: Optional[int]) -> str:
    parts = [source, symbol, interval]
    if start:
        parts.append(start.strftime("%Y%m%d"))
    if end:
        parts.append(end.strftime("%Y%m%d"))
    if lookback_days is not None:
        parts.append(f"lb{lookback_days}")
    raw = "|".join(str(p) for p in parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


class CacheLayer:
    """Read/write parquet cache for OHLCV DataFrames."""

    def __init__(self, cache_dir: str):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.parquet"

    def get(
        self,
        source: str,
        symbol: str,
        interval: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        lookback_days: Optional[int] = None,
    ) -> Optional[pd.DataFrame]:
        key = _cache_key(source, symbol, interval, start, end, lookback_days)
        p = self.path(key)
        if not p.exists():
            return None
        try:
            df = pd.read_parquet(p)
            # Parquet does not persist tz; we always store UTC, so restore on read
            if not df.empty and hasattr(df.index, "tz") and df.index.tz is None:
                df.index = df.index.tz_localize("UTC", ambiguous="infer")
            return df
        except Exception:
            return None

    def set(
        self,
        df: pd.DataFrame,
        source: str,
        symbol: str,
        interval: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        lookback_days: Optional[int] = None,
    ) -> str:
        key = _cache_key(source, symbol, interval, start, end, lookback_days)
        p = self.path(key)
        df = df.copy()
        if df.index.tz is not None:
            df.index = df.index.tz_convert("UTC")
        df.to_parquet(p, index=True)
        return key

    def invalidate(
        self,
        source: str,
        symbol: str,
        interval: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        lookback_days: Optional[int] = None,
    ) -> bool:
        key = _cache_key(source, symbol, interval, start, end, lookback_days)
        p = self.path(key)
        if p.exists():
            p.unlink()
            return True
        return False
