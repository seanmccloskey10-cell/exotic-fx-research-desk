"""Smoke tests for the candlestick + volume component.

These are pure offline tests — no network. Verify the component returns a
valid Plotly figure for sane input and None for empty input, and that the
up/down coloring picks the right volume colors per bar.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from components.candlestick_chart import GAIN, LOSS, candlestick_chart


def _sample_df() -> pd.DataFrame:
    idx = pd.date_range("2026-04-01", periods=5, freq="D")
    return pd.DataFrame(
        {
            "Open": [100, 102, 101, 103, 105],
            "High": [103, 104, 103, 106, 107],
            "Low": [99, 100, 100, 102, 104],
            "Close": [102, 101, 103, 105, 104],  # up, down, up, up, down
            "Volume": [1000, 1200, 900, 1500, 1100],
        },
        index=idx,
    )


def test_returns_plotly_figure():
    fig = candlestick_chart(_sample_df(), title="TEST")
    assert isinstance(fig, go.Figure)


def test_empty_input_returns_none():
    assert candlestick_chart(None) is None
    assert candlestick_chart(pd.DataFrame()) is None


def test_figure_has_candlestick_and_volume_traces():
    fig = candlestick_chart(_sample_df())
    trace_types = [type(t).__name__ for t in fig.data]
    assert "Candlestick" in trace_types
    assert "Bar" in trace_types


def test_volume_bar_colors_track_open_close():
    fig = candlestick_chart(_sample_df())
    bar = next(t for t in fig.data if type(t).__name__ == "Bar")
    # Close >= Open → GAIN, else LOSS. Sample pattern: up, down, up, up, down.
    expected = [GAIN, LOSS, GAIN, GAIN, LOSS]
    assert list(bar.marker.color) == expected


def test_no_rangeslider():
    fig = candlestick_chart(_sample_df())
    # Rangeslider hides duplicate controls when Streamlit already handles zoom.
    assert fig.layout.xaxis.rangeslider.visible is False
