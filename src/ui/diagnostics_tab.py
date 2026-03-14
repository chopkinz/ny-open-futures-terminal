"""Data Diagnostics tab: quality, time range, schema, cache. Times in display TZ with AM/PM."""
from __future__ import annotations

import pandas as pd  # pyright: ignore[reportMissingImports]
import streamlit as st  # pyright: ignore[reportMissingImports]

from src.utils.format import format_int
from src.utils.time import format_timestamp_12h


def render_diagnostics_tab(
    df: pd.DataFrame,
    data_source: str,
    cache_dir: str,
    symbol: str,
    interval: str,
    display_tz,
) -> None:
    st.markdown("#### Data diagnostics")
    st.markdown("")
    if df.empty:
        st.warning("No data loaded. Run analysis from the sidebar.")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Data quality**")
        row_count = len(df)
        dupes = int(df.index.duplicated().sum())
        null_open = int(df["open"].isna().sum())
        null_high = int(df["high"].isna().sum())
        null_low = int(df["low"].isna().sum())
        null_close = int(df["close"].isna().sum())
        st.metric("Rows", format_int(row_count))
        st.metric("Duplicate timestamps", format_int(dupes))
        st.write(f"Nulls: open {format_int(null_open)}, high {format_int(null_high)}, low {format_int(null_low)}, close {format_int(null_close)}.")
        st.markdown("")
        st.markdown("**Time range**")
        first_ts = df.index.min()
        last_ts = df.index.max()
        st.metric("First bar", format_timestamp_12h(first_ts, display_tz))
        st.metric("Last bar", format_timestamp_12h(last_ts, display_tz))
        tz = str(df.index.tz) if hasattr(df.index, "tz") and df.index.tz else "None (naive)"
        st.metric("Data timezone", tz)

    with col2:
        st.markdown("**Source & cache**")
        st.metric("Data source", data_source)
        st.metric("Symbol", symbol.replace("=F", ""))
        st.metric("Interval", interval)
        st.write("Cache directory:")
        st.code(cache_dir, language=None)
    st.markdown("")
    st.caption("Parquet cache is used when enabled; refresh from the sidebar to re-fetch.")
