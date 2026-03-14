"""
Price chart for a single day with OR levels overlay.
Day Explorer: clearly shows OR high/low, entry, stop, target, exit — high contrast.
"""
from __future__ import annotations

from typing import Optional

import pandas as pd
import plotly.graph_objects as go

from src.constants import OHLCV_CLOSE, OHLCV_HIGH, OHLCV_LOW, OHLCV_OPEN

# Palette (works on light and dark)
COLOR_OR_HIGH = "#06b6d4"
COLOR_OR_LOW = "#f59e0b"
COLOR_OR_MID = "#71717a"
COLOR_ENTRY = "#22c55e"
COLOR_STOP = "#ef4444"
COLOR_TARGET = "#10b981"
COLOR_EXIT = "#e4e4e7"
COLOR_UP = "#22c55e"
COLOR_DOWN = "#ef4444"

from src.charts.common import LAYOUT

# Day chart taller; hide range slider
LAYOUT_DAY = {**LAYOUT, "height": 500, "xaxis_rangeslider_visible": False}


def plot_day_price(
    df: pd.DataFrame,
    or_high: Optional[float] = None,
    or_low: Optional[float] = None,
    or_mid: Optional[float] = None,
    entry: Optional[float] = None,
    stop: Optional[float] = None,
    target: Optional[float] = None,
    exit_price: Optional[float] = None,
    title: Optional[str] = None,
) -> go.Figure:
    """Candlestick with horizontal levels; OR high/low, entry, stop, target, exit clearly labeled."""
    if df.empty or len(df) < 2:
        fig = go.Figure()
        fig.update_layout(**LAYOUT_DAY, title=dict(text=title or "No data", font=dict(size=14)))
        return fig

    df = df.sort_index()
    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df[OHLCV_OPEN],
            high=df[OHLCV_HIGH],
            low=df[OHLCV_LOW],
            close=df[OHLCV_CLOSE],
            name="Price",
            increasing_line_color=COLOR_UP,
            decreasing_line_color=COLOR_DOWN,
        )
    )

    # Horizontal levels with clear labels and consistent line width
    level_configs = []
    if or_high is not None:
        level_configs.append((or_high, "OR High", COLOR_OR_HIGH, "dash", 2))
    if or_low is not None:
        level_configs.append((or_low, "OR Low", COLOR_OR_LOW, "dash", 2))
    if or_mid is not None:
        level_configs.append((or_mid, "OR Mid", COLOR_OR_MID, "dot", 1))
    if entry is not None:
        level_configs.append((entry, "Entry", COLOR_ENTRY, "solid", 2))
    if stop is not None:
        level_configs.append((stop, "Stop", COLOR_STOP, "solid", 2))
    if target is not None:
        level_configs.append((target, "Target", COLOR_TARGET, "solid", 2))
    if exit_price is not None:
        level_configs.append((exit_price, "Exit", COLOR_EXIT, "dash", 2))

    for level, label, color, dash, width in level_configs:
        fig.add_hline(
            y=level,
            line_dash=dash,
            line_color=color,
            line_width=width,
            annotation_text=label,
            annotation_position="right",
            annotation_font_size=11,
            annotation_font_color=color,
        )

    fig.update_layout(
        **LAYOUT_DAY,
        title=dict(text=title or "Session", font=dict(size=14)),
    )
    return fig


def plot_data_preview(df: pd.DataFrame, title: str = "Data we analyzed (close)") -> go.Figure:
    """Line chart of close price for the full loaded dataset (Yahoo or other source)."""
    if df.empty or OHLCV_CLOSE not in df.columns:
        fig = go.Figure()
        fig.update_layout(**LAYOUT, title=dict(text=title, font=dict(size=14)))
        return fig
    df = df.sort_index()
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df[OHLCV_CLOSE],
            mode="lines",
            name="Close",
            line=dict(color="#2563eb", width=1.2),
        )
    )
    fig.update_layout(
        **{**LAYOUT, "height": 280, "xaxis_rangeslider_visible": False},
        title=dict(text=title, font=dict(size=14)),
        yaxis_title="Close",
    )
    return fig
