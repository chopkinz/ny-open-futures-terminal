"""
Data validation and normalization for OHLCV DataFrames.
"""
from __future__ import annotations

from typing import Optional

import pandas as pd

from src.constants import OHLCV_CLOSE, OHLCV_COLUMNS, OHLCV_HIGH, OHLCV_LOW, OHLCV_OPEN, OHLCV_VOLUME

# Common aliases from different sources
COLUMN_ALIASES = {
    "Open": OHLCV_OPEN,
    "High": OHLCV_HIGH,
    "Low": OHLCV_LOW,
    "Close": OHLCV_CLOSE,
    "Volume": OHLCV_VOLUME,
    "open": OHLCV_OPEN,
    "high": OHLCV_HIGH,
    "low": OHLCV_LOW,
    "close": OHLCV_CLOSE,
    "volume": OHLCV_VOLUME,
}


def normalize_ohlcv_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns to standard open, high, low, close, volume."""
    out = df.copy()
    rename = {}
    for c in out.columns:
        if c in COLUMN_ALIASES:
            rename[c] = COLUMN_ALIASES[c]
    out = out.rename(columns=rename)
    return out


def validate_ohlcv(df: pd.DataFrame, strict: bool = True) -> tuple[bool, str]:
    """
    Validate DataFrame has required OHLCV columns and basic sanity.
    Returns (ok, error_message).
    """
    for col in OHLCV_COLUMNS:
        if col not in df.columns:
            return False, f"Missing column: {col}"
    required = [OHLCV_OPEN, OHLCV_HIGH, OHLCV_LOW, OHLCV_CLOSE]
    for col in required:
        if df[col].isna().all():
            return False, f"All NaN in column: {col}"
    # High >= Low
    if (df[OHLCV_HIGH] < df[OHLCV_LOW]).any():
        return False, "High must be >= Low for all rows"
    if strict and df.index.duplicated().any():
        return False, "Duplicate timestamps in index"
    return True, ""


def dedupe_sort_index(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate index, keep first occurrence, sort ascending."""
    out = df[~df.index.duplicated(keep="first")].sort_index()
    return out


def prepare_ohlcv(
    df: pd.DataFrame,
    normalize: bool = True,
    validate: bool = True,
    dedupe: bool = True,
) -> pd.DataFrame:
    """Normalize, dedupe, sort, and validate. Returns prepared DataFrame or raises."""
    if df.empty:
        return df
    if normalize:
        df = normalize_ohlcv_columns(df)
    if dedupe:
        df = dedupe_sort_index(df)
    if validate:
        ok, msg = validate_ohlcv(df, strict=True)
        if not ok:
            raise ValueError(msg)
    return df
