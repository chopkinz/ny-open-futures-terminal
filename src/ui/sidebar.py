"""
Sidebar: data, session, strategy, run. Session times in 12h AM/PM; display timezone for all times.
"""
from __future__ import annotations

import streamlit as st

from src.config import build_data_config, build_session_config, build_strategy_config


def _yahoo_intraday_limit_warning(interval: str, lookback_days: int) -> str | None:
    """Return user-facing warning when Yahoo intraday history is limited, else None."""
    if interval in ("1m", "2m") and lookback_days > 7:
        return (
            "**Yahoo intraday limit:** 1m and 2m data are limited to about **7 calendar days**. "
            "Use 5m or higher for longer backtests, or reduce lookback to 7 days."
        )
    if interval in ("1m", "2m"):
        return (
            "**Yahoo limit:** 1m/2m only provide ~7 days of history. "
            "Switch to 5m or 15m for more history."
        )
    return None


def render_sidebar() -> tuple:
    """Render sidebar and return (data_config, session_config, strategy_config, run_clicked, display_tz_key, auto_optimize, optimize_metric, balance, risk_pct)."""
    st.sidebar.markdown("### Your account")
    st.sidebar.markdown("")
    balance = st.sidebar.number_input(
        "Current balance ($)",
        min_value=0.0,
        value=50000.0,
        step=1000.0,
        format="%.0f",
        help="Used to size risk and estimate expected profit.",
    )
    risk_pct = st.sidebar.number_input(
        "Risk % per trade",
        min_value=0.1,
        max_value=10.0,
        value=1.0,
        step=0.5,
        format="%.1f",
        help="Risk this % of balance per trade (e.g. 1 = 1%).",
    )
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Setup")
    st.sidebar.markdown("")
    symbol = st.sidebar.selectbox(
        "Symbol",
        ["MNQ=F", "NQ=F", "MES=F", "ES=F"],
        index=0,
        format_func=lambda x: x.replace("=F", ""),
    )
    lookback_days = st.sidebar.number_input(
        "Days of data",
        min_value=5,
        max_value=365,
        value=7,
        step=5,
        help="How far back to analyze.",
    )
    st.sidebar.markdown("**Opening range (CST)**")
    c1, c2 = st.sidebar.columns(2)
    with c1:
        or_start = st.text_input("OR start", value="8:00 AM", label_visibility="collapsed", placeholder="8:00 AM")
    with c2:
        or_end = st.text_input("OR end", value="8:15 AM", label_visibility="collapsed", placeholder="8:15 AM")
    auto_optimize = st.sidebar.checkbox(
        "Auto-optimize target (best R from data)",
        value=True,
        help="Find the best target R from history; recommended.",
    )
    st.sidebar.markdown("")
    run = st.sidebar.button("▶ Run analysis", type="primary", use_container_width=True)

    # Advanced: collapsed by default; widgets still run and supply values
    optimize_metric = "win_rate"
    with st.sidebar.expander("Advanced settings"):
        display_tz_key = st.selectbox(
            "Display timezone",
            ["Local", "America/New_York", "America/Chicago", "UTC"],
            index=0,
        )
        optimize_metric = st.selectbox(
            "Optimize for",
            ["expectancy_r", "win_rate"],
            index=0,
            format_func=lambda x: "Expectancy (highest $ per trade)" if x == "expectancy_r" else "Win rate (closest to 100%)",
        )
        st.markdown("Data")
        data_source = st.selectbox(
            "Source",
            ["yahoo", "databento"],
            index=0,
            format_func=lambda x: "Yahoo (free)" if x == "yahoo" else "Databento (paid)",
            help="Yahoo is free; no API key needed. Databento requires a paid subscription.",
            label_visibility="collapsed",
        )
        interval = st.selectbox("Interval", ["1m", "2m", "5m", "15m", "30m", "60m"], index=2)
        refresh_cache = st.checkbox("Refresh cache", value=False)
        warning = _yahoo_intraday_limit_warning(interval, lookback_days)
        if warning:
            st.warning(warning)
        st.markdown("Session")
        trade_window_end = st.text_input("Trade window end", value="12:00 PM")
        st.markdown("Strategy")
        strategy_mode = st.selectbox(
            "Mode",
            ["orb", "failed_breakout", "sweep_reversal"],
            index=0,
            format_func=lambda x: {"orb": "ORB", "failed_breakout": "Failed breakout", "sweep_reversal": "Sweep & reversal"}.get(x, x),
        )
        entry_mode = st.selectbox(
            "Entry",
            ["touch", "close_beyond", "breakout_retest"],
            index=1,
            format_func=lambda x: {"touch": "Touch", "close_beyond": "Close beyond", "breakout_retest": "Breakout + retest"}.get(x, x),
        )
        stop_mode = st.selectbox(
            "Stop",
            ["opposite_or_side", "fixed_or_multiple", "atr_based", "fixed_points"],
            index=0,
            format_func=lambda x: {"opposite_or_side": "Opposite OR", "fixed_or_multiple": "OR multiple", "atr_based": "ATR", "fixed_points": "Fixed pts"}.get(x, x),
        )
        target_mode = st.selectbox(
            "Target",
            ["fixed_r", "opposite_side", "session_close", "trailing_placeholder"],
            index=0,
            format_func=lambda x: {"fixed_r": "Fixed R", "opposite_side": "Opposite OR", "session_close": "Session close", "trailing_placeholder": "Trailing"}.get(x, x),
        )
        r_multiple = st.number_input("Target R", min_value=0.5, max_value=5.0, value=1.0, step=0.25)
        one_trade_per_day = st.checkbox("One trade per day", value=True)
        direction_filter = st.selectbox("Direction", ["both", "long", "short"], index=0)
        with st.expander("Costs"):
            slippage_ticks = st.number_input("Slippage (ticks)", min_value=0.0, value=0.0, step=0.5)
            fee_per_side = st.number_input("Fee per side ($)", min_value=0.0, value=0.0, step=0.5)

    data_config = build_data_config({
        "source": data_source,
        "symbol": symbol,
        "interval": interval,
        "lookback_days": lookback_days,
        "refresh_cache": refresh_cache,
    })
    session_config = build_session_config({
        "or_start": or_start,
        "or_end": or_end,
        "trade_window_end": trade_window_end,
    })
    strategy_config = build_strategy_config({
        "mode": strategy_mode,
        "entry_mode": entry_mode,
        "stop_mode": stop_mode,
        "target_mode": target_mode,
        "r_multiple": r_multiple,
        "one_trade_per_day": one_trade_per_day,
        "direction_filter": direction_filter,
        "slippage_ticks": slippage_ticks,
        "fee_per_side": fee_per_side,
    })

    return data_config, session_config, strategy_config, run, display_tz_key, auto_optimize, optimize_metric, balance, risk_pct
