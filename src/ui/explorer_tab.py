"""Day Explorer tab: session selector, price chart, session summary. Times in display TZ with AM/PM."""
from __future__ import annotations

from datetime import date as date_type

import pandas as pd
import streamlit as st

from src.charts.price import plot_day_price
from src.models import OpeningRange, TradeRecord
from src.sessions.engine import SessionEngine
from src.utils.time import format_timestamp_12h


def render_explorer_tab(
    df: pd.DataFrame,
    or_map: dict[str, OpeningRange],
    trades: list[TradeRecord],
    session_engine: SessionEngine,
    display_tz,
) -> None:
    st.markdown("#### Day explorer")
    st.markdown("")
    if df.empty or not or_map:
        st.info("Load data and run analysis first.")
        return

    dates = sorted(or_map.keys())
    chosen = st.selectbox(
        "Select session",
        dates,
        index=min(len(dates) - 1, 0),
        format_func=lambda x: x,
    )
    or_ = or_map.get(chosen)
    if not or_:
        return
    try:
        session_d = date_type.fromisoformat(chosen)
    except Exception:
        session_d = pd.Timestamp(chosen).date()
    day_bars = session_engine.slice_session(df, session_d)
    if day_bars.empty:
        st.warning(f"No bars for {chosen}.")
        return

    day_trades = [t for t in trades if t.trade_date == chosen]
    entry = stop = target = exit_p = None
    if day_trades:
        t0 = day_trades[0]
        entry, stop, target, exit_p = t0.entry_price, t0.stop_price, t0.target_price, t0.exit_price

    st.markdown("**Price chart**")
    st.markdown("")
    fig = plot_day_price(
        day_bars,
        or_high=or_.or_high,
        or_low=or_.or_low,
        or_mid=or_.or_mid,
        entry=entry,
        stop=stop,
        target=target,
        exit_price=exit_p,
        title=chosen,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("OR high/low, entry, stop, target, exit (when a trade was taken).")
    st.markdown("")
    st.markdown("---")
    st.markdown("**Session summary**")
    st.markdown("")
    narrative = _narrative(chosen, or_, day_trades, display_tz)
    st.write(narrative)


def _narrative(date_str: str, or_: OpeningRange, day_trades: list[TradeRecord], display_tz) -> str:
    from src.backtest.metrics import pnl_dollars
    from src.utils.format import format_currency, format_r

    parts = [f"**{date_str}** — OR width: {or_.or_width:.2f} pts (high {or_.or_high:.2f}, low {or_.or_low:.2f})."]
    if not day_trades:
        parts.append("No strategy trade triggered.")
        return " ".join(parts)
    t = day_trades[0]
    entry_time_str = format_timestamp_12h(t.entry_ts, display_tz)
    exit_time_str = format_timestamp_12h(t.exit_ts, display_tz)
    pnl_str = format_currency(pnl_dollars(t), 0)
    parts.append(f"Direction: {t.direction}. Entry {t.entry_price:.2f} at {entry_time_str}, exit {t.exit_price:.2f} at {exit_time_str} ({t.exit_reason}).")
    if t.r_multiple is not None:
        parts.append(f"Result: {format_r(t.r_multiple)}, PnL {pnl_str}.")
    else:
        parts.append(f"PnL {pnl_str}.")
    return " ".join(parts)
