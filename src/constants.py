"""
Constants for NY Open Futures Terminal.
"""
from typing import Final

# Standard OHLCV column names (normalized)
OHLCV_OPEN: Final[str] = "open"
OHLCV_HIGH: Final[str] = "high"
OHLCV_LOW: Final[str] = "low"
OHLCV_CLOSE: Final[str] = "close"
OHLCV_VOLUME: Final[str] = "volume"
OHLCV_COLUMNS: Final[tuple[str, ...]] = (OHLCV_OPEN, OHLCV_HIGH, OHLCV_LOW, OHLCV_CLOSE, OHLCV_VOLUME)

# Yahoo symbol mapping for display
SYMBOL_DISPLAY: Final[dict[str, str]] = {
    "MNQ=F": "MNQ",
    "NQ=F": "NQ",
    "MES=F": "MES",
    "ES=F": "ES",
}

# Supported intervals (minutes)
INTERVAL_MINUTES: Final[dict[str, int]] = {
    "1m": 1,
    "2m": 2,
    "5m": 5,
    "15m": 15,
    "30m": 30,
    "60m": 60,
}

# Default timezone for session logic
DEFAULT_TZ: Final[str] = "America/New_York"

# Exit reasons
EXIT_REASON_STOP: Final[str] = "stop"
EXIT_REASON_TARGET: Final[str] = "target"
EXIT_REASON_SESSION_CLOSE: Final[str] = "session_close"
EXIT_REASON_CANCEL: Final[str] = "cancel"
EXIT_REASON_NO_FILL: Final[str] = "no_fill"

# Setup types
SETUP_ORB: Final[str] = "orb"
SETUP_FAILED_BREAKOUT: Final[str] = "failed_breakout"
SETUP_SWEEP_REVERSAL: Final[str] = "sweep_reversal"
