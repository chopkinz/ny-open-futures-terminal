"""
Pydantic and dataclass models for NY Open Futures Terminal.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# --- Enums ---
class DataSource(str, Enum):
    YAHOO = "yahoo"
    DATABENTO = "databento"


class Direction(str, Enum):
    LONG = "long"
    SHORT = "short"


class EntryMode(str, Enum):
    TOUCH = "touch"
    CLOSE_BEYOND = "close_beyond"
    BREAKOUT_RETEST = "breakout_retest"


class StopMode(str, Enum):
    OPPOSITE_OR_SIDE = "opposite_or_side"
    FIXED_OR_MULTIPLE = "fixed_or_multiple"
    ATR_BASED = "atr_based"
    FIXED_POINTS = "fixed_points"


class TargetMode(str, Enum):
    FIXED_R = "fixed_r"
    OPPOSITE_SIDE = "opposite_side"
    SESSION_CLOSE = "session_close"
    TRAILING_PLACEHOLDER = "trailing_placeholder"


class StrategyMode(str, Enum):
    ORB = "orb"
    FAILED_BREAKOUT = "failed_breakout"
    SWEEP_REVERSAL = "sweep_reversal"
    TIME_OF_DAY = "time_of_day"
    PREMARKET_CONTEXT = "premarket_context"


# --- Pydantic config models ---
class SessionConfig(BaseModel):
    timezone: str = "America/Chicago"
    or_start: str = "08:00"
    or_end: str = "09:15"
    trade_window_end: str = "12:00"
    premarket_start: str = "04:00"
    premarket_end: str = "09:29"
    ny_open: str = "09:30"


class StrategyConfig(BaseModel):
    mode: StrategyMode = StrategyMode.ORB
    entry_mode: EntryMode = EntryMode.CLOSE_BEYOND
    stop_mode: StopMode = StopMode.OPPOSITE_OR_SIDE
    target_mode: TargetMode = TargetMode.FIXED_R
    r_multiple: float = 1.0
    stop_or_multiple: float = 1.0
    buffer_ticks: float = 0.0
    slippage_ticks: float = 0.0
    fee_per_side: float = 0.0
    one_trade_per_day: bool = True
    direction_filter: str = "both"
    max_wait_minutes: int = 120
    fixed_stop_points: Optional[float] = None
    fixed_target_points: Optional[float] = None


class DataConfig(BaseModel):
    source: DataSource = DataSource.YAHOO
    symbol: str = "MNQ=F"
    interval: str = "5m"
    lookback_days: int = 90
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    cache_dir: str = "data/cache"
    use_cache: bool = True
    refresh_cache: bool = False


# --- Trade and backtest records ---
@dataclass
class OpeningRange:
    """Opening range for a single day."""
    date: str  # NY date YYYY-MM-DD
    or_high: float
    or_low: float
    or_mid: float
    or_width: float
    or_start_ts: datetime
    or_end_ts: datetime
    bar_count: int
    or_volume: float = 0.0  # total volume during OR bars (if available)


@dataclass
class TradeRecord:
    """Single simulated trade."""
    trade_date: str
    symbol: str
    setup_type: str
    direction: str
    entry_ts: Optional[datetime]
    entry_price: Optional[float]
    stop_price: Optional[float]
    target_price: Optional[float]
    exit_ts: Optional[datetime]
    exit_price: Optional[float]
    exit_reason: str
    mae: Optional[float] = None
    mfe: Optional[float] = None
    r_multiple: Optional[float] = None
    pnl_points: Optional[float] = None
    pnl_dollars: Optional[float] = None
    holding_seconds: Optional[float] = None
    triggered: bool = True
    invalidated: bool = False
    or_high: Optional[float] = None
    or_low: Optional[float] = None
    or_width: Optional[float] = None
    volume_at_entry: Optional[float] = None  # volume on the entry bar (morning breakout)


@dataclass
class PerformanceSummary:
    """Aggregate backtest performance."""
    total_trades: int
    winning_trades: int
    losing_trades: int
    breakeven_trades: int
    win_rate: float
    loss_rate: float
    breakeven_rate: float
    expectancy_r: float
    avg_r: float
    median_r: float
    total_r: float
    gross_profit: float
    gross_loss: float
    profit_factor: float
    avg_hold_seconds: float
    max_drawdown: float
    max_win_streak: int
    max_loss_streak: int
    trades: list[TradeRecord] = field(default_factory=list)


@dataclass
class ContractSpec:
    """Futures contract specification."""
    symbol_root: str
    point_value: float
    tick_size: float
    tick_value: float
