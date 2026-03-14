"""
Equity curve and drawdown charts. Light theme (white/blue) by default.
"""
from __future__ import annotations

from typing import List

import plotly.graph_objects as go

from src.backtest.metrics import pnl_dollars
from src.charts.common import LAYOUT
from src.models import TradeRecord


def plot_equity_curve(trades: List[TradeRecord], title: str = "Equity Curve") -> go.Figure:
    """Cumulative PnL in dollars over trade sequence."""
    valid = [t for t in trades if t.triggered and t.exit_price is not None]
    if not valid:
        fig = go.Figure()
        fig.add_annotation(text="No trades", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(color="#64748b"))
        fig.update_layout(**LAYOUT, title=dict(text=title, font=dict(size=14)))
        return fig
    cumulative = []
    acc = 0.0
    for t in valid:
        acc += pnl_dollars(t)
        cumulative.append(acc)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=list(range(len(cumulative))),
            y=cumulative,
            mode="lines+markers",
            line=dict(color="#2563eb", width=2),
            name="Equity",
        )
    )
    fig.update_layout(
        **LAYOUT,
        title=dict(text=title, font=dict(size=14)),
        xaxis_title="Trade #",
        yaxis_title="Cumulative PnL",
        yaxis_tickformat="$,.0f",
    )
    return fig


def plot_drawdown(trades: List[TradeRecord], title: str = "Drawdown") -> go.Figure:
    """Drawdown from peak equity."""
    valid = [t for t in trades if t.triggered and t.exit_price is not None]
    if not valid:
        fig = go.Figure()
        fig.update_layout(**LAYOUT, title=dict(text=title, font=dict(size=14)), height=320)
        return fig
    equity = 0.0
    peak = 0.0
    dd = []
    for t in valid:
        equity += pnl_dollars(t)
        peak = max(peak, equity)
        dd.append(peak - equity)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=list(range(len(dd))),
            y=dd,
            fill="tozeroy",
            line=dict(color="#ef4444"),
            name="Drawdown",
        )
    )
    fig.update_layout(
        **LAYOUT,
        title=dict(text=title, font=dict(size=14)),
        xaxis_title="Trade #",
        yaxis_title="Drawdown",
        yaxis_tickformat="$,.0f",
    )
    return fig
