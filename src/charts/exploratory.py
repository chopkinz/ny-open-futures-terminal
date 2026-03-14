"""
Exploratory charts: R distribution, OR width vs R, weekday. Light theme.
"""
from __future__ import annotations

from datetime import datetime
from typing import List

import numpy as np
import plotly.graph_objects as go

from src.charts.common import LAYOUT
from src.models import TradeRecord


def plot_r_histogram(trades: List[TradeRecord], nbins: int = 24, title: str = "R Multiple Distribution") -> go.Figure:
    """Histogram of R multiples."""
    r_vals = [t.r_multiple for t in trades if t.r_multiple is not None]
    if not r_vals:
        fig = go.Figure()
        fig.update_layout(**LAYOUT, title=dict(text=title, font=dict(size=14)))
        return fig
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=r_vals, nbinsx=nbins, marker_color="#2563eb", name="R", opacity=0.85))
    fig.update_layout(
        **LAYOUT,
        title=dict(text=title, font=dict(size=14)),
        xaxis_title="R multiple",
        yaxis_title="Count",
    )
    return fig


def plot_or_width_vs_r(
    trades: List[TradeRecord],
    title: str = "OR Width vs R Multiple",
) -> go.Figure:
    """Scatter: OR width (x) vs R multiple (y)."""
    points = [(t.or_width, t.r_multiple) for t in trades if t.or_width is not None and t.r_multiple is not None]
    if not points:
        fig = go.Figure()
        fig.update_layout(**LAYOUT, title=dict(text=title, font=dict(size=14)))
        return fig
    x, y = zip(*points)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="markers",
            marker=dict(size=8, color=list(y), colorscale="RdYlGn", showscale=True, colorbar=dict(title="R")),
            name="Trades",
        )
    )
    fig.add_hline(y=0, line_dash="dash", line_color="#94a3b8")
    fig.update_layout(
        **LAYOUT,
        title=dict(text=title, font=dict(size=14)),
        xaxis_title="OR width (points)",
        yaxis_title="R multiple",
    )
    return fig


def plot_weekday_heatmap(trades: List[TradeRecord], title: str = "Results by Weekday") -> go.Figure:
    """Bar chart of avg R by weekday."""
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    by_day = {d: [] for d in weekdays}
    for t in trades:
        if t.r_multiple is None:
            continue
        try:
            dt = datetime.fromisoformat(t.trade_date)
            idx = dt.weekday()
            if idx < 5:
                by_day[weekdays[idx]].append(t.r_multiple)
        except Exception:
            continue
    avg_r = [np.mean(by_day[d]) if by_day[d] else 0 for d in weekdays]
    fig = go.Figure(go.Bar(x=weekdays, y=avg_r, marker_color="#2563eb", name="Avg R", opacity=0.9))
    fig.update_layout(
        **{
            **LAYOUT,
            "title": dict(text=title, font=dict(size=14)),
            "xaxis_title": "Weekday",
            "yaxis_title": "Avg R",
            "height": 320,
        }
    )
    return fig
