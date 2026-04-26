"""Candlestick + volume chart — Plotly subplots, dark-theme native.

Upper panel: OHLC candles. Lower panel (25% of height): volume bars,
colored green on up-days and red on down-days. X-axis unified hover.
No rangeslider (Streamlit already provides chart interactivity).
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

GAIN = "#16A34A"
LOSS = "#DC2626"
FLAT = "#6B7280"
GRID = "#2A2E36"


def candlestick_chart(
    ohlcv: pd.DataFrame,
    title: str = "",
    height: int = 520,
) -> Optional[go.Figure]:
    """Render OHLCV data as candlesticks on top of a volume subplot.

    `ohlcv` must have columns Open, High, Low, Close, Volume and a
    DatetimeIndex. Returns None for empty input so the caller can show
    an "unavailable" state instead.
    """
    if ohlcv is None or ohlcv.empty:
        return None

    # Per-bar color: green if close >= open, red otherwise. Used for volume bars.
    up = ohlcv["Close"] >= ohlcv["Open"]
    volume_colors = [GAIN if u else LOSS for u in up]

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.78, 0.22],
        specs=[[{"type": "candlestick"}], [{"type": "bar"}]],
    )

    fig.add_trace(
        go.Candlestick(
            x=ohlcv.index,
            open=ohlcv["Open"],
            high=ohlcv["High"],
            low=ohlcv["Low"],
            close=ohlcv["Close"],
            name=title or "Price",
            increasing=dict(line=dict(color=GAIN), fillcolor=GAIN),
            decreasing=dict(line=dict(color=LOSS), fillcolor=LOSS),
            showlegend=False,
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Bar(
            x=ohlcv.index,
            y=ohlcv["Volume"],
            marker=dict(color=volume_colors, line=dict(width=0)),
            name="Volume",
            showlegend=False,
            hovertemplate="Vol %{y:,.0f}<extra></extra>",
        ),
        row=2,
        col=1,
    )

    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
        dragmode="pan",
        xaxis=dict(
            rangeslider=dict(visible=False),
            gridcolor=GRID,
            showgrid=True,
        ),
        xaxis2=dict(
            gridcolor=GRID,
            showgrid=True,
        ),
        yaxis=dict(
            gridcolor=GRID,
            tickprefix="$",
            showgrid=True,
        ),
        yaxis2=dict(
            gridcolor=GRID,
            showgrid=True,
            title=None,
        ),
    )

    return fig
