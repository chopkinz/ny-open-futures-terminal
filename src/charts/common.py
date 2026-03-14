"""
Shared Plotly layout. Default: clean white and blue light theme.
"""
from __future__ import annotations

# Light theme (default): white background, blue/gray accents
LAYOUT_LIGHT = dict(
    paper_bgcolor="#ffffff",
    plot_bgcolor="#f8fafc",
    font=dict(color="#0f172a", size=12),
    xaxis=dict(
        gridcolor="#e2e8f0",
        zerolinecolor="#e2e8f0",
        showgrid=True,
        title_font=dict(size=12),
        tickfont=dict(size=11),
    ),
    yaxis=dict(
        gridcolor="#e2e8f0",
        zerolinecolor="#e2e8f0",
        showgrid=True,
        title_font=dict(size=12),
        tickfont=dict(size=11),
    ),
    margin=dict(l=56, r=48, t=48, b=44),
    showlegend=True,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        bgcolor="rgba(255,255,255,0.95)",
        bordercolor="#e2e8f0",
        font=dict(size=11),
    ),
    height=380,
)

# Default layout for all charts
LAYOUT = LAYOUT_LIGHT
LAYOUT_DARK = dict(
    paper_bgcolor="#0a0a0a",
    plot_bgcolor="#141414",
    font=dict(color="#f4f4f5", size=12),
    xaxis=dict(gridcolor="#27272a", zerolinecolor="#27272a", showgrid=True, title_font=dict(size=12), tickfont=dict(size=11)),
    yaxis=dict(gridcolor="#27272a", zerolinecolor="#27272a", showgrid=True, title_font=dict(size=12), tickfont=dict(size=11)),
    margin=dict(l=56, r=48, t=48, b=44),
    showlegend=True,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(20,20,20,0.9)", bordercolor="#27272a", font=dict(size=11)),
    height=380,
)
