"""Trade Log tab: filters, formatted table with entry/exit times (AM/PM), PnL in $, export."""
from __future__ import annotations

import pandas as pd  # pyright: ignore[reportMissingImports]
import streamlit as st  # pyright: ignore[reportMissingImports]

from src.models import TradeRecord
from src.ui.backtest_tab import _trades_to_dataframe
from src.utils.format import format_currency
from src.utils.time import format_timestamp_12h


def render_trade_log_tab(trades: list[TradeRecord], display_tz) -> None:
    st.markdown("#### Trade log")
    st.markdown("")
    if not trades:
        st.info("No trades to show. Run analysis to generate a trade log.")
        return

    df = _trades_to_dataframe(trades)
    df["entry_time"] = df["entry_ts"].apply(lambda ts: format_timestamp_12h(ts, display_tz))
    df["exit_time"] = df["exit_ts"].apply(lambda ts: format_timestamp_12h(ts, display_tz))
    filter_col1, filter_col2, _ = st.columns([1, 1, 2])
    with filter_col1:
        direction = st.selectbox("Direction", ["All", "Long", "Short"], index=0, label_visibility="collapsed")
    with filter_col2:
        exit_filter = st.selectbox("Exit reason", ["All", "Stop", "Target", "Session close", "No fill"], index=0, label_visibility="collapsed")
    if direction != "All":
        df = df[df["direction"] == direction.lower()]
    if exit_filter != "All":
        reason_map = {"Stop": "stop", "Target": "target", "Session close": "session_close", "No fill": "no_fill"}
        df = df[df["exit_reason"] == reason_map.get(exit_filter, exit_filter)]
    show_cols = ["date", "symbol", "setup", "direction", "entry_time", "exit_time", "entry_price", "exit_price", "exit_reason", "R", "pnl_dollars", "PnL_pts", "hold_sec", "OR_width"]
    display_df = df[[c for c in show_cols if c in df.columns]].rename(columns={
        "date": "Date",
        "symbol": "Symbol",
        "setup": "Setup",
        "direction": "Direction",
        "entry_time": "Entry time",
        "exit_time": "Exit time",
        "entry_price": "Entry",
        "exit_price": "Exit",
        "exit_reason": "Exit reason",
        "R": "R",
        "pnl_dollars": "PnL",
        "PnL_pts": "PnL (pts)",
        "hold_sec": "Hold (s)",
        "OR_width": "OR width",
    })
    if "PnL" in display_df.columns:
        display_df["PnL"] = display_df["PnL"].apply(lambda x: format_currency(x, 0) if x is not None and pd.notna(x) else "—")
    for col in ["Entry", "Exit", "R", "PnL (pts)", "OR width"]:
        if col in display_df.columns:
            display_df[col] = display_df[col].round(2)
    st.markdown("")
    st.dataframe(display_df, use_container_width=True, height=480)
    st.markdown("")
    st.download_button(
        "Export to CSV",
        data=display_df.to_csv(index=False).encode("utf-8"),
        file_name="trade_log.csv",
        mime="text/csv",
    )
