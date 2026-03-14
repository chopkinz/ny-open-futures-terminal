"""Backtest tab: summary metrics, distributions, trade log with entry/exit times (AM/PM), export."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from src.backtest.metrics import pnl_dollars
from src.charts.exploratory import plot_r_histogram, plot_or_width_vs_r, plot_weekday_heatmap
from src.models import PerformanceSummary, TradeRecord
from src.utils.format import format_currency, format_r
from src.utils.time import format_timestamp_12h


def render_backtest_tab(perf: PerformanceSummary, display_tz) -> None:
    if perf.total_trades == 0:
        st.info("Run analysis to see backtest results.")
        return

    st.markdown("#### Summary")
    st.markdown("")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Wins", f"{perf.winning_trades:,}")
        st.metric("Losses", f"{perf.losing_trades:,}")
    with c2:
        st.metric("Avg R", format_r(perf.avg_r))
        st.metric("Median R", format_r(perf.median_r))
    with c3:
        st.metric("Total R", format_r(perf.total_r))
        st.metric("Avg hold", f"{perf.avg_hold_seconds / 60:.1f} min")
    with c4:
        st.metric("Max drawdown", format_currency(perf.max_drawdown, 0))
        st.metric("Best / worst streak", f"{perf.max_win_streak} / {perf.max_loss_streak}")
    st.markdown("")
    st.markdown("---")
    st.markdown("#### Distributions")
    st.markdown("")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(plot_r_histogram(perf.trades), use_container_width=True)
    with col2:
        st.plotly_chart(plot_or_width_vs_r(perf.trades), use_container_width=True)
    st.plotly_chart(plot_weekday_heatmap(perf.trades), use_container_width=True)
    st.markdown("")
    st.markdown("---")
    st.markdown("#### Trade log")
    st.markdown("")
    df = _trades_to_dataframe(perf.trades)
    df["entry_time"] = df["entry_ts"].apply(lambda ts: format_timestamp_12h(ts, display_tz))
    df["exit_time"] = df["exit_ts"].apply(lambda ts: format_timestamp_12h(ts, display_tz))
    display_df = df.rename(columns={
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
    st.dataframe(display_df, use_container_width=True, height=400)
    st.download_button(
        "Export to CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="backtest_trade_log.csv",
        mime="text/csv",
    )


def _trades_to_dataframe(trades: list[TradeRecord]) -> pd.DataFrame:
    rows = []
    for t in trades:
        pnl_d = pnl_dollars(t)
        rows.append({
            "date": t.trade_date,
            "symbol": t.symbol,
            "setup": t.setup_type,
            "direction": t.direction,
            "entry_ts": t.entry_ts,
            "exit_ts": t.exit_ts,
            "entry_price": t.entry_price,
            "exit_price": t.exit_price,
            "exit_reason": t.exit_reason,
            "R": t.r_multiple,
            "PnL_pts": t.pnl_points,
            "pnl_dollars": pnl_d,
            "hold_sec": t.holding_seconds,
            "OR_width": t.or_width,
        })
    return pd.DataFrame(rows)
