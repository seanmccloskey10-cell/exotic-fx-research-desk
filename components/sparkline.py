"""Inline sparkline mini-chart — stub for Phase 2.

Phase 1 renders the watchlist table without inline sparklines.
Phase 2 will add a Plotly sparkline per row per PRD §13.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
import plotly.graph_objects as go


def sparkline(prices: pd.Series, height: int = 40) -> Optional[go.Figure]:
    """Return a minimal Plotly figure for inline rendering, or None if empty."""
    if prices is None or prices.empty:
        return None
    fig = go.Figure(
        data=[
            go.Scatter(
                x=list(range(len(prices))),
                y=prices.values,
                mode="lines",
                line=dict(width=1.5),
                hoverinfo="skip",
            )
        ]
    )
    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    return fig
