"""Time-of-Day Analysis tab: entry hour stats, readability. Terminal-style hierarchy."""
from __future__ import annotations

import numpy as np  # pyright: ignore[reportMissingImports]
import streamlit as st  # pyright: ignore[reportMissingImports]

from src.models import PerformanceSummary
from src.utils.format import format_r


def render_time_tab(perf: PerformanceSummary) -> None:
    st.markdown("#### Time-of-day analysis")
    st.markdown("")
    if perf.total_trades == 0:
        st.info("Run analysis to see time-of-day stats.")
        return

    by_hour: dict[int, list[float]] = {}
    for t in perf.trades:
        if t.entry_ts is None or t.r_multiple is None:
            continue
        h = t.entry_ts.hour if hasattr(t.entry_ts, "hour") else 0
        by_hour.setdefault(h, []).append(t.r_multiple)
    if not by_hour:
        st.caption("No entry timestamps available for time-of-day breakdown.")
        return
    st.markdown("**Avg R by entry hour**")
    st.markdown("")
    hours = sorted(by_hour.keys())
    n_cols = 5
    for i in range(0, len(hours), n_cols):
        cols = st.columns(n_cols)
        for j, c in enumerate(cols):
            idx = i + j
            if idx < len(hours):
                h = hours[idx]
                vals = by_hour[h]
                avg_r = float(np.mean(vals))
                with c:
                    st.metric(f"{h:02d}:00", format_r(avg_r), delta=f"n={len(vals)}")
    st.markdown("")
    st.caption("Breakout timing and session high/low timing charts in a future release.")
