"""
Configuration loader for NY Open Futures Terminal.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from src.constants import DEFAULT_TZ
from src.utils.time import parse_time_to_24h
from src.models import (
    DataConfig,
    DataSource,
    EntryMode,
    SessionConfig,
    StopMode,
    StrategyConfig,
    StrategyMode,
    TargetMode,
)


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_yaml(path: Path) -> dict[str, Any]:
    """Load YAML file into dict."""
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def get_defaults() -> dict[str, Any]:
    """Load default config from config/defaults.yaml."""
    root = _project_root()
    cfg_path = root / "config" / "defaults.yaml"
    return load_yaml(cfg_path)


def build_session_config(overrides: dict[str, Any] | None = None) -> SessionConfig:
    """Build SessionConfig from defaults and overrides."""
    defaults = get_defaults()
    s = defaults.get("sessions", {})
    cfg = {
        "timezone": s.get("timezone", DEFAULT_TZ),
        "or_start": s.get("default_or_start", "09:30"),
        "or_end": s.get("default_or_end", "09:35"),
        "trade_window_end": s.get("trade_window_end", "12:00"),
        "premarket_start": s.get("premarket_start", "04:00"),
        "premarket_end": s.get("premarket_end", "09:29"),
        "ny_open": s.get("ny_open", "09:30"),
    }
    if overrides:
        cfg.update({k: v for k, v in overrides.items() if k in cfg})
    # Normalize time strings to 24h so "9:30 AM" -> "09:30"
    for key in ("or_start", "or_end", "trade_window_end", "premarket_start", "premarket_end", "ny_open"):
        if key in cfg and isinstance(cfg[key], str):
            cfg[key] = parse_time_to_24h(cfg[key])
    return SessionConfig(**cfg)


def build_strategy_config(overrides: dict[str, Any] | None = None) -> StrategyConfig:
    """Build StrategyConfig from defaults and overrides."""
    defaults = get_defaults()
    s = defaults.get("strategy", {})
    b = defaults.get("backtest", {})
    cfg = {
        "mode": StrategyMode(s.get("default_mode", "orb")),
        "entry_mode": EntryMode(s.get("entry_modes", ["close_beyond"])[0]),
        "stop_mode": StopMode(s.get("stop_modes", ["opposite_or_side"])[0]),
        "target_mode": TargetMode(s.get("target_modes", ["fixed_r"])[0]),
        "r_multiple": b.get("default_r_multiple", 1.0),
        "stop_or_multiple": b.get("default_stop_or_multiple", 1.0),
        "buffer_ticks": b.get("default_buffer_ticks", 0),
        "slippage_ticks": s.get("default_slippage_ticks", 0),
        "fee_per_side": s.get("default_fee_per_side", 0),
        "one_trade_per_day": s.get("one_trade_per_day", True),
        "direction_filter": s.get("direction_filter", "both"),
        "max_wait_minutes": s.get("max_wait_minutes", 120),
    }
    if overrides:
        for k, v in overrides.items():
            if k == "mode" and isinstance(v, str):
                cfg["mode"] = StrategyMode(v)
            elif k == "entry_mode" and isinstance(v, str):
                cfg["entry_mode"] = EntryMode(v)
            elif k == "stop_mode" and isinstance(v, str):
                cfg["stop_mode"] = StopMode(v)
            elif k == "target_mode" and isinstance(v, str):
                cfg["target_mode"] = TargetMode(v)
            elif k in cfg:
                cfg[k] = v
    return StrategyConfig(**cfg)


def build_data_config(overrides: dict[str, Any] | None = None) -> DataConfig:
    """Build DataConfig from defaults and overrides."""
    defaults = get_defaults()
    d = defaults.get("data", {})
    root = _project_root()
    cache_dir = d.get("cache_dir", "data/cache")
    if not os.path.isabs(cache_dir):
        cache_dir = str(root / cache_dir)
    cfg = {
        "source": DataSource(d.get("default_source", "yahoo")),
        "symbol": d.get("default_symbol", "MNQ=F"),
        "interval": d.get("default_interval", "5m"),
        "lookback_days": d.get("default_lookback_days", 90),
        "cache_dir": cache_dir,
        "use_cache": True,
        "refresh_cache": False,
    }
    if overrides:
        for k, v in overrides.items():
            if k == "source" and isinstance(v, str):
                cfg["source"] = DataSource(v)
            elif k in cfg:
                cfg[k] = v
            elif k in ("start_date", "end_date"):
                cfg[k] = v
    return DataConfig(**cfg)


def get_contract_specs() -> dict[str, dict[str, float]]:
    """Return contract specs from defaults."""
    defaults = get_defaults()
    return defaults.get("contracts", {})
