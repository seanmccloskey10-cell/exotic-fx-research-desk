"""Patterns (Educational) tab — reference library of common chart formations.

This is deliberately not a detection engine. We do not scan the watchlist,
flag pattern matches, or assign confidence scores. Every chart here is built
on synthesized price data so the pattern is unambiguous — the user sees
exactly what a textbook version looks like and reads plain-English notes
about what it means and when it fails.

If we ever add actual pattern detection, it belongs in a different surface
with its own false-positive handling.
"""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from config.settings import Settings
from config.theme import page_header
from data_sources.orchestrator import DataOrchestrator

GRID = "#2A2E36"
PRICE = "#E5E7EB"
BULL = "#16A34A"
BEAR = "#DC2626"
NEUTRAL = "#9CA3AF"
HIGHLIGHT = "#F59E0B"


def _base_layout(title: str) -> dict:
    return dict(
        height=340,
        margin=dict(l=0, r=0, t=44, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            gridcolor=GRID,
            showticklabels=False,
            title=dict(text="Time →", font=dict(size=10, color=NEUTRAL)),
            zeroline=False,
        ),
        yaxis=dict(
            gridcolor=GRID,
            title=dict(text="Price", font=dict(size=10, color=NEUTRAL)),
            zeroline=False,
        ),
        showlegend=False,
        title=dict(
            text=title,
            x=0.01,
            y=0.97,
            font=dict(size=13, color="#E5E7EB"),
        ),
        font=dict(family="Segoe UI Variable, -apple-system, sans-serif", size=11),
    )


def _price_trace(y: np.ndarray) -> go.Scatter:
    return go.Scatter(
        x=np.arange(len(y)),
        y=y,
        mode="lines",
        line=dict(color=PRICE, width=2.2, shape="spline", smoothing=0.3),
        hoverinfo="skip",
    )


# ---------- Pattern 1: Head & Shoulders ----------

def _head_and_shoulders_fig() -> go.Figure:
    x = np.arange(60)
    y = np.piecewise(
        x.astype(float),
        [
            x < 10,
            (x >= 10) & (x < 18),
            (x >= 18) & (x < 25),
            (x >= 25) & (x < 33),
            (x >= 33) & (x < 40),
            (x >= 40) & (x < 48),
            x >= 48,
        ],
        [
            lambda t: 100 + (t / 10) * 10,            # rise into left shoulder
            lambda t: 110 - ((t - 10) / 8) * 8,       # left shoulder down to neckline
            lambda t: 102 + ((t - 18) / 7) * 18,      # up into head peak (120)
            lambda t: 120 - ((t - 25) / 8) * 18,      # head down to neckline (102)
            lambda t: 102 + ((t - 33) / 7) * 10,      # right shoulder up (~112)
            lambda t: 112 - ((t - 40) / 8) * 10,      # right shoulder down
            lambda t: 102 - ((t - 48) / 12) * 14,     # breakdown below neckline
        ],
    )
    fig = go.Figure(_price_trace(y))
    # Neckline
    fig.add_shape(
        type="line", x0=10, x1=59, y0=102, y1=102,
        line=dict(color=HIGHLIGHT, width=1.5, dash="dash"),
    )
    # Annotations — peaks
    fig.add_annotation(x=14, y=112, text="Left shoulder", showarrow=True, arrowhead=1, ay=-30)
    fig.add_annotation(x=22, y=122, text="Head", showarrow=True, arrowhead=1, ay=-30)
    fig.add_annotation(x=44, y=114, text="Right shoulder", showarrow=True, arrowhead=1, ay=-30)
    fig.add_annotation(x=30, y=102, text="Neckline", showarrow=False, yshift=-15, font=dict(color=HIGHLIGHT))
    fig.add_annotation(x=56, y=92, text="Breakdown", showarrow=True, arrowhead=2, ay=-30, font=dict(color=BEAR))
    fig.update_layout(**_base_layout("Head and Shoulders — bearish reversal"))
    return fig


# ---------- Pattern 2: Double Top ----------

def _double_top_fig() -> go.Figure:
    x = np.arange(60)
    y = np.piecewise(
        x.astype(float),
        [x < 15, (x >= 15) & (x < 25), (x >= 25) & (x < 40), (x >= 40) & (x < 50), x >= 50],
        [
            lambda t: 100 + (t / 15) * 25,              # rise to first peak (125)
            lambda t: 125 - ((t - 15) / 10) * 12,       # pullback to ~113
            lambda t: 113 + ((t - 25) / 15) * 12,       # rise back to 125 (second peak)
            lambda t: 125 - ((t - 40) / 10) * 15,       # decline from second peak
            lambda t: 110 - ((t - 50) / 10) * 10,       # continuation down
        ],
    )
    fig = go.Figure(_price_trace(y))
    fig.add_shape(
        type="line", x0=0, x1=59, y0=125, y1=125,
        line=dict(color=HIGHLIGHT, width=1.5, dash="dash"),
    )
    fig.add_annotation(x=15, y=127, text="Peak 1", showarrow=True, arrowhead=1, ay=-25)
    fig.add_annotation(x=40, y=127, text="Peak 2", showarrow=True, arrowhead=1, ay=-25)
    fig.add_annotation(x=30, y=125, text="Resistance", showarrow=False, yshift=10, font=dict(color=HIGHLIGHT))
    fig.add_annotation(x=55, y=103, text="Breakdown", showarrow=True, arrowhead=2, ay=-30, font=dict(color=BEAR))
    fig.update_layout(**_base_layout("Double Top — bearish reversal (flip for Double Bottom)"))
    return fig


# ---------- Pattern 3: Cup and Handle ----------

def _cup_and_handle_fig() -> go.Figure:
    x = np.arange(70)
    # Cup: parabolic U-shape from bar 0 to ~45
    cup_x = np.arange(45)
    cup_y = 110 - 15 * np.cos(np.pi * cup_x / 44)  # starts at 95, bottoms, returns to 125
    # Actually simpler: parabolic
    cup_y = 110 - 20 * (1 - ((cup_x - 22) / 22) ** 2)
    # Handle: mild pullback from bar 45 to 55
    handle_x = np.arange(45, 55)
    handle_y = np.linspace(cup_y[-1], cup_y[-1] - 4, len(handle_x))
    # Breakout
    breakout_x = np.arange(55, 70)
    breakout_y = np.linspace(handle_y[-1], handle_y[-1] + 14, len(breakout_x))
    y = np.concatenate([cup_y, handle_y, breakout_y])
    fig = go.Figure(_price_trace(y))
    fig.add_shape(
        type="line", x0=0, x1=69, y0=cup_y[0], y1=cup_y[0],
        line=dict(color=HIGHLIGHT, width=1.5, dash="dash"),
    )
    fig.add_annotation(x=22, y=cup_y.min() - 1, text="Cup", showarrow=True, arrowhead=1, ay=30)
    fig.add_annotation(x=50, y=handle_y.min() - 1, text="Handle", showarrow=True, arrowhead=1, ay=30)
    fig.add_annotation(x=5, y=cup_y[0], text="Rim / resistance", showarrow=False, yshift=10, font=dict(color=HIGHLIGHT))
    fig.add_annotation(x=66, y=breakout_y[-1] + 1, text="Breakout", showarrow=True, arrowhead=2, ay=-30, font=dict(color=BULL))
    fig.update_layout(**_base_layout("Cup and Handle — bullish continuation"))
    return fig


# ---------- Pattern 4: Flag / Pennant ----------

def _flag_fig() -> go.Figure:
    x = np.arange(60)
    # Pole: sharp rise from bar 0-12
    pole = np.linspace(100, 125, 13)
    # Flag: sideways chop from bar 13-30
    chop_x = np.arange(13, 30)
    chop_y = 124 + np.sin(chop_x) * 1.5 + np.cos(chop_x * 0.7) * 0.8
    # Breakout: continuation rise from bar 30-59
    breakout = np.linspace(chop_y[-1], chop_y[-1] + 15, 30)
    y = np.concatenate([pole, chop_y, breakout])
    fig = go.Figure(_price_trace(y))
    # Parallel channel lines over the flag
    fig.add_shape(
        type="line", x0=13, x1=29, y0=127, y1=126,
        line=dict(color=HIGHLIGHT, width=1.2, dash="dot"),
    )
    fig.add_shape(
        type="line", x0=13, x1=29, y0=122, y1=121,
        line=dict(color=HIGHLIGHT, width=1.2, dash="dot"),
    )
    fig.add_annotation(x=6, y=112, text="Pole", showarrow=True, arrowhead=1, ax=-30, ay=20)
    fig.add_annotation(x=21, y=130, text="Flag", showarrow=True, arrowhead=1, ay=-20)
    fig.add_annotation(x=50, y=135, text="Continuation", showarrow=True, arrowhead=2, ay=30, font=dict(color=BULL))
    fig.update_layout(**_base_layout("Flag / Pennant — short-term continuation"))
    return fig


# ---------- Pattern 5: Ascending Triangle ----------

def _ascending_triangle_fig() -> go.Figure:
    x = np.arange(60)
    resistance = 125
    # Rising support line: y = 95 + 0.6x
    # Price oscillates between rising support and flat resistance, then breaks out
    bounces = [0, 10, 22, 34, 44]
    y = np.empty(60)
    for i in range(60):
        if i < 44:
            # Oscillate: higher lows, fixed highs
            support = 95 + 0.6 * i
            if i in (10, 22, 34):  # highs
                y[i] = resistance - 0.5
            elif i in (5, 16, 28, 40):  # lows
                y[i] = support
            else:
                # interpolate between
                y[i] = (support + resistance) / 2 + np.sin(i * 0.6) * 4
        else:
            # Breakout above resistance
            y[i] = resistance + (i - 44) * 1.1
    fig = go.Figure(_price_trace(y))
    fig.add_shape(
        type="line", x0=0, x1=44, y0=resistance, y1=resistance,
        line=dict(color=HIGHLIGHT, width=1.5, dash="dash"),
    )
    fig.add_shape(
        type="line", x0=0, x1=44, y0=95, y1=95 + 0.6 * 44,
        line=dict(color=HIGHLIGHT, width=1.5, dash="dash"),
    )
    fig.add_annotation(x=22, y=resistance, text="Resistance", showarrow=False, yshift=10, font=dict(color=HIGHLIGHT))
    fig.add_annotation(x=30, y=108, text="Higher lows", showarrow=False, font=dict(color=HIGHLIGHT))
    fig.add_annotation(x=55, y=y[-1], text="Breakout", showarrow=True, arrowhead=2, ay=-30, font=dict(color=BULL))
    fig.update_layout(**_base_layout("Ascending Triangle — bullish breakout (flip for Descending)"))
    return fig


# ---------- Render ----------

_PATTERNS = [
    {
        "name": "Head and Shoulders",
        "bias": "Bearish reversal",
        "fig": _head_and_shoulders_fig,
        "what": (
            "Three peaks: a left shoulder, a higher central peak (the head), then a "
            "right shoulder roughly the same height as the left. The two lows between "
            "the peaks define a horizontal or near-horizontal **neckline**."
        ),
        "means": (
            "When price breaks below the neckline after the right shoulder, the pattern "
            "is considered complete. It typically signals that an uptrend has exhausted "
            "and a downtrend is starting. The depth of the head is often used as a rough "
            "target for how far price might fall below the neckline."
        ),
        "fails": (
            "Fails often — maybe 30–40% of the time. Common failure: price dips below "
            "the neckline briefly then rebounds above it (a **false breakdown**). "
            "Traders usually want to see volume expand on the breakdown; a quiet break "
            "is suspect. Inverse pattern (Inverse Head and Shoulders) is bullish."
        ),
    },
    {
        "name": "Double Top / Double Bottom",
        "bias": "Reversal",
        "fig": _double_top_fig,
        "what": (
            "Two peaks (Double Top) or two troughs (Double Bottom) at roughly the same "
            "price, separated by a pullback. The level the price keeps bouncing off of "
            "is the **resistance** (tops) or **support** (bottoms)."
        ),
        "means": (
            "The market tested a level twice and failed to break through. Confirmation "
            "comes when price breaks in the opposite direction — below the pullback low "
            "(Double Top → bearish) or above the pullback high (Double Bottom → bullish). "
            "The distance between the peaks/troughs and the pullback is often used as "
            "a rough price target after the break."
        ),
        "fails": (
            "One of the most common chart patterns — and also one of the most over-called. "
            "Real Double Tops take time to form (weeks, not days). Two peaks on tight "
            "timeframes are often just noise. Look for the two peaks to be close in "
            "price but separated by a meaningful pullback before trusting the pattern."
        ),
    },
    {
        "name": "Cup and Handle",
        "bias": "Bullish continuation",
        "fig": _cup_and_handle_fig,
        "what": (
            "A rounded U-shaped dip and recovery (the **cup**), followed by a shallow "
            "pullback near the cup's rim (the **handle**). The handle is usually smaller "
            "than the cup — a short consolidation, not a full reversal."
        ),
        "means": (
            "Made famous by William O'Neil. Interpreted as an orderly shake-out of weak "
            "holders during the cup, followed by a final consolidation in the handle. "
            "A breakout above the cup's rim on rising volume is the confirmation signal; "
            "the depth of the cup is often used as a rough price target."
        ),
        "fails": (
            "Cups that are too V-shaped (sharp drop, sharp bounce) tend to fail more often "
            "than smooth U-shaped cups — the V implies panic, not accumulation. Handles "
            "that retrace more than a third of the cup's depth are a warning sign that the "
            "uptrend may be done, not just pausing."
        ),
    },
    {
        "name": "Flag / Pennant",
        "bias": "Continuation (direction of preceding trend)",
        "fig": _flag_fig,
        "what": (
            "A sharp directional move (the **pole**) followed by a short, tight "
            "consolidation (the **flag** or **pennant**) in a narrow range, then a "
            "continuation in the original direction. Flags are roughly parallel channels; "
            "pennants are small symmetric triangles. The shapes are close cousins."
        ),
        "means": (
            "The pole represents strong momentum and the flag is a brief pause as the "
            "market digests the move. A breakout in the direction of the pole — up for "
            "bull flags, down for bear flags — is the signal. The pole's length is often "
            "added to the breakout point as a target."
        ),
        "fails": (
            "Flags work best when short — typically 1 to 4 weeks. A \"flag\" that drags "
            "on for months is just a range, not a flag, and loses its predictive value. "
            "Flags against very strong macro moves (earnings, Fed) can also fail — the "
            "pattern is a short-term signal, not an override of larger forces."
        ),
    },
    {
        "name": "Ascending / Descending Triangle",
        "bias": "Breakout continuation",
        "fig": _ascending_triangle_fig,
        "what": (
            "A horizontal support or resistance line paired with a rising or falling "
            "trendline, creating a narrowing triangle. **Ascending**: flat resistance on "
            "top, rising support below. **Descending**: flat support below, falling "
            "resistance on top."
        ),
        "means": (
            "Ascending triangles are typically read as bullish — buyers keep stepping in "
            "at higher lows, and eventually exhaust sellers sitting at the horizontal "
            "resistance. Descending triangles read as bearish for the mirror reason. "
            "The breakout direction usually (but not always) matches the bias."
        ),
        "fails": (
            "Triangles can break either way — the bias is a probability, not a certainty. "
            "Best practice is to wait for the actual breakout and some volume confirmation "
            "rather than predicting the direction in advance. Triangles that form over too "
            "few touches (fewer than 2 highs + 2 lows) aren't reliable patterns at all."
        ),
    },
]


def _render_card(pat: dict) -> None:
    """Render one pattern card: chart, title, bias, and a compact details expander.

    Wrapped in `st.container(border=True)` so each pattern sits visually
    inside its own bordered box — otherwise the chart + heading + body text
    read as loose elements stacked on the page rather than one unit.
    """
    with st.container(border=True):
        fig = pat["fig"]()
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown(f"#### {pat['name']}")
        st.caption(pat["bias"])
        st.markdown(pat["what"])
        with st.expander("What it usually means · when it fails"):
            st.markdown(f"**What it usually means.** {pat['means']}")
            st.markdown(f"**When it fails.** {pat['fails']}")


def render(settings: Settings, orch: DataOrchestrator) -> None:
    page_header(
        "Patterns (Educational)",
        "A reference library of common chart patterns — synthesized data, unambiguous shapes. "
        "This tab does not scan your watchlist or generate signals; it teaches what these "
        "formations look like.",
    )

    st.info(
        "**How to read this page.** Each card has a chart, what the pattern is, and a "
        "collapsed detail panel for what it usually means + when it fails. No single "
        "pattern is a trade signal on its own; they're hypotheses that need volume, "
        "context, and confirmation before acting."
    )

    # Two-column grid so every pattern is visible at once — Roula shouldn't
    # have to click five times to see what the patterns look like.
    for i in range(0, len(_PATTERNS), 2):
        cols = st.columns(2, gap="large")
        with cols[0]:
            _render_card(_PATTERNS[i])
        if i + 1 < len(_PATTERNS):
            with cols[1]:
                _render_card(_PATTERNS[i + 1])
