"""
Trade execution simulation: bar-by-bar fill, stop, target. No lookahead.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

import pandas as pd  # pyright: ignore[reportMissingImports]
import pytz  # pyright: ignore[reportMissingModuleSource]

from src.constants import (
    EXIT_REASON_NO_FILL,
    EXIT_REASON_SESSION_CLOSE,
    EXIT_REASON_STOP,
    EXIT_REASON_TARGET,
    OHLCV_CLOSE,
    OHLCV_HIGH,
    OHLCV_LOW,
    OHLCV_VOLUME,
    SETUP_ORB,
)
from src.models import OpeningRange, StrategyConfig, TradeRecord
from src.sessions.engine import SessionEngine
from src.utils.math_utils import r_multiple
from src.utils.time import trade_window_end_ts

NY = pytz.timezone("America/New_York")
DEFAULT_TICK_SIZE = 0.25


def _apply_buffer(level: float, direction: str, buffer_ticks: float, tick_size: float) -> float:
    if buffer_ticks <= 0 or tick_size <= 0:
        return level
    buf = buffer_ticks * tick_size
    return level + buf if direction == "long" else level - buf


def _stop_price(or_high: float, or_low: float, direction: str, config: StrategyConfig, tick_size: float = 0.25) -> float:
    if config.fixed_stop_points is not None:
        return (or_high if direction == "short" else or_low) + (
            config.fixed_stop_points * tick_size if direction == "short" else -config.fixed_stop_points * tick_size
        )
    if config.stop_mode.value == "opposite_or_side":
        return or_low if direction == "long" else or_high
    if config.stop_mode.value == "fixed_or_multiple":
        width = or_high - or_low
        add = config.stop_or_multiple * width
        return or_low - add if direction == "long" else or_high + add
    return or_low if direction == "long" else or_high


def _target_price(
    entry: float,
    or_high: float,
    or_low: float,
    direction: str,
    config: StrategyConfig,
    tick_size: float = 0.25,
) -> float:
    if config.fixed_target_points is not None:
        add = config.fixed_target_points * tick_size
        return entry + add if direction == "long" else entry - add
    if config.target_mode.value == "opposite_side":
        return or_low if direction == "long" else or_high
    # fixed_r
    stop = _stop_price(or_high, or_low, direction, config, tick_size)
    risk = abs(entry - stop)
    r = config.r_multiple
    return entry + r * risk if direction == "long" else entry - r * risk


def run_day_orb(
    df: pd.DataFrame,
    session_d: date,
    or_: OpeningRange,
    session_config,
    strategy_config: StrategyConfig,
    symbol: str = "MNQ=F",
    tick_size: float = 0.25,
) -> list[TradeRecord]:
    """
    Simulate ORB for one day. After OR end, detect first break (high or low),
    then simulate entry and exit. No lookahead.
    """
    # Require timezone-aware index to avoid ambiguous comparisons
    if df.index.tz is None:
        return []
    or_end_ts = or_.or_end_ts.astimezone(df.index.tz)
    trade_end_ts = trade_window_end_ts(session_d, session_config.trade_window_end, session_config.timezone).astimezone(df.index.tz)
    # Restrict to session_d so we never use bars from another session (e.g. overnight gap)
    def _to_date(x):
        if hasattr(x, "date") and callable(getattr(x, "date")):
            return x.date()
        return x
    engine = SessionEngine(session_config)
    session_dates = engine.session_dates_from_index(df.index)
    session_mask = session_dates.apply(_to_date) == session_d
    df_session = df.loc[session_mask]
    # Bars after OR end and before trade window end (no lookahead)
    after_or = df_session.loc[(df_session.index > or_end_ts) & (df_session.index <= trade_end_ts)]
    if after_or.empty:
        return []

    dir_filter = (strategy_config.direction_filter or "both").lower()
    buffer = strategy_config.buffer_ticks or 0
    or_high_buf = _apply_buffer(or_.or_high, "long", buffer, tick_size)
    or_low_buf = _apply_buffer(or_.or_low, "short", buffer, tick_size)
    close_beyond = strategy_config.entry_mode.value == "close_beyond"

    # First pass: find first bar where long breaks and first bar where short breaks (morning breakout = highest volume)
    first_long_ts: Optional[datetime] = None
    first_long_entry: Optional[float] = None
    first_long_volume: Optional[float] = None
    first_short_ts: Optional[datetime] = None
    first_short_entry: Optional[float] = None
    first_short_volume: Optional[float] = None
    for idx, row in after_or.iterrows():
        high, low, close = row[OHLCV_HIGH], row[OHLCV_LOW], row[OHLCV_CLOSE]
        vol = float(row[OHLCV_VOLUME]) if OHLCV_VOLUME in row.index else None
        if first_long_ts is None and dir_filter in ("both", "long"):
            if close_beyond and close > or_high_buf:
                first_long_ts = idx
                first_long_entry = close
                first_long_volume = vol
            elif not close_beyond and high >= or_high_buf:
                first_long_ts = idx
                first_long_entry = or_high_buf
                first_long_volume = vol
        if first_short_ts is None and dir_filter in ("both", "short"):
            if close_beyond and close < or_low_buf:
                first_short_ts = idx
                first_short_entry = close
                first_short_volume = vol
            elif not close_beyond and low <= or_low_buf:
                first_short_ts = idx
                first_short_entry = or_low_buf
                first_short_volume = vol
        if first_long_ts is not None and first_short_ts is not None:
            break

    # Take chronologically first break (or only allowed direction)
    take_long = first_long_ts is not None and (dir_filter == "long" or (dir_filter == "both" and (first_short_ts is None or first_long_ts <= first_short_ts)))
    take_short = first_short_ts is not None and (dir_filter == "short" or (dir_filter == "both" and (first_long_ts is None or first_short_ts < first_long_ts)))

    trades = []
    if take_long and first_long_ts is not None and first_long_entry is not None:
        tr = _simulate_trade(
            df=df_session,
            entry_ts=first_long_ts,
            entry_price=first_long_entry,
            direction="long",
            or_=or_,
            session_d=session_d,
            strategy_config=strategy_config,
            symbol=symbol,
            trade_end_ts=trade_end_ts,
            tick_size=tick_size,
            volume_at_entry=first_long_volume,
        )
        if tr and tr.triggered:
            trades.append(tr)
    if not strategy_config.one_trade_per_day and take_short and first_short_ts is not None and first_short_entry is not None:
        tr = _simulate_trade(
            df=df_session,
            entry_ts=first_short_ts,
            entry_price=first_short_entry,
            direction="short",
            or_=or_,
            session_d=session_d,
            strategy_config=strategy_config,
            symbol=symbol,
            trade_end_ts=trade_end_ts,
            tick_size=tick_size,
            volume_at_entry=first_short_volume,
        )
        if tr and tr.triggered:
            trades.append(tr)
    return trades


def _simulate_trade(
    df: pd.DataFrame,
    entry_ts: datetime,
    entry_price: float,
    direction: str,
    or_: OpeningRange,
    session_d: date,
    strategy_config: StrategyConfig,
    symbol: str,
    trade_end_ts: datetime,
    tick_size: float = 0.25,
    volume_at_entry: Optional[float] = None,
) -> Optional[TradeRecord]:
    """From entry, simulate bar-by-bar until stop, target, or session end."""
    # Slippage
    slip = (strategy_config.slippage_ticks or 0) * tick_size
    if direction == "long":
        entry_price = entry_price + slip
    else:
        entry_price = entry_price - slip

    stop_price = _stop_price(or_.or_high, or_.or_low, direction, strategy_config, tick_size)
    target_price = _target_price(entry_price, or_.or_high, or_.or_low, direction, strategy_config, tick_size)
    if strategy_config.target_mode.value == "session_close":
        target_price = None  # will exit at session close

    # df here is already restricted to session_d (passed from run_day_orb)
    after_entry = df.loc[df.index > entry_ts]
    after_entry = after_entry.loc[after_entry.index <= trade_end_ts]
    if after_entry.empty:
        return TradeRecord(
            trade_date=session_d.isoformat(),
            symbol=symbol,
            setup_type=SETUP_ORB,
            direction=direction,
            entry_ts=entry_ts,
            entry_price=entry_price,
            stop_price=stop_price,
            target_price=target_price or 0,
            exit_ts=entry_ts,
            exit_price=entry_price,
            exit_reason=EXIT_REASON_NO_FILL,
            triggered=True,
            or_high=or_.or_high,
            or_low=or_.or_low,
            or_width=or_.or_width,
            volume_at_entry=volume_at_entry,
        )

    mae, mfe = 0.0, 0.0
    exit_ts = None
    exit_price = None
    exit_reason = EXIT_REASON_SESSION_CLOSE
    for idx, row in after_entry.iterrows():
        high, low, close = row[OHLCV_HIGH], row[OHLCV_LOW], row[OHLCV_CLOSE]
        if direction == "long":
            mae = min(mae, low - entry_price)
            mfe = max(mfe, high - entry_price)
            if low <= stop_price:
                exit_ts = idx
                exit_price = stop_price
                exit_reason = EXIT_REASON_STOP
                break
            if target_price and high >= target_price:
                exit_ts = idx
                exit_price = target_price
                exit_reason = EXIT_REASON_TARGET
                break
        else:
            mae = min(mae, entry_price - high)
            mfe = max(mfe, entry_price - low)
            if high >= stop_price:
                exit_ts = idx
                exit_price = stop_price
                exit_reason = EXIT_REASON_STOP
                break
            if target_price and low <= target_price:
                exit_ts = idx
                exit_price = target_price
                exit_reason = EXIT_REASON_TARGET
                break

    if exit_ts is None:
        # Session close
        last = after_entry.iloc[-1]
        exit_ts = after_entry.index[-1]
        exit_price = last[OHLCV_CLOSE]
        exit_reason = EXIT_REASON_SESSION_CLOSE

    risk = abs(entry_price - stop_price)
    r_mult = r_multiple(entry_price, exit_price, stop_price, direction) if risk > 0 else None
    pnl_points = (exit_price - entry_price) if direction == "long" else (entry_price - exit_price)
    holding = (exit_ts - entry_ts).total_seconds() if hasattr(exit_ts - entry_ts, "total_seconds") else 0

    return TradeRecord(
        trade_date=session_d.isoformat(),
        symbol=symbol,
        setup_type=SETUP_ORB,
        direction=direction,
        entry_ts=entry_ts,
        entry_price=entry_price,
        stop_price=stop_price,
        target_price=target_price or 0,
        exit_ts=exit_ts,
        exit_price=exit_price,
        exit_reason=exit_reason,
        mae=mae,
        mfe=mfe,
        r_multiple=r_mult,
        pnl_points=pnl_points,
        holding_seconds=holding,
        triggered=True,
        invalidated=False,
        volume_at_entry=volume_at_entry,
        or_high=or_.or_high,
        or_low=or_.or_low,
        or_width=or_.or_width,
    )
