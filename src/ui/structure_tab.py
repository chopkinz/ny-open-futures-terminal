"""Structure Analytics tab: opening range stats, setup breakdown."""
from __future__ import annotations

import numpy as np  # pyright: ignore[reportMissingImports]
import streamlit as st  # pyright: ignore[reportMissingImports]

from src.models import PerformanceSummary
from src.utils.format import format_float, format_int


def render_structure_tab(perf: PerformanceSummary, or_map: dict) -> None:
    st.markdown("#### Opening range & structure")
    st.markdown("")
    if not or_map:
        st.info("Run analysis to populate structure stats.")
        return

    or_widths = [o.or_width for o in or_map.values()]
    st.markdown("**Opening range stats**")
    st.markdown("")
    s1, s2, s3 = st.columns(3)
    with s1:
        st.metric("Sessions with OR", format_int(len(or_map)))
    with s2:
        st.metric("Avg OR width", f"{format_float(float(np.mean(or_widths)))} pts" if or_widths else "—")
    with s3:
        st.metric("Min / max OR width", f"{format_float(min(or_widths))} / {format_float(max(or_widths))} pts" if or_widths else "—")
    st.markdown("")
    if perf.total_trades > 0:
        st.markdown("**Setup breakdown**")
        st.markdown("")
        longs = sum(1 for t in perf.trades if t.direction == "long")
        shorts = sum(1 for t in perf.trades if t.direction == "short")
        b1, b2 = st.columns(2)
        with b1:
            st.metric("Long setups", format_int(longs))
        with b2:
            st.metric("Short setups", format_int(shorts))
    st.markdown("")
    st.caption("First-break %, sweep %, and failed-break analytics will expand in a future release.")
