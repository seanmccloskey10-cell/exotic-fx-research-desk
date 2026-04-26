"""Peer-rank bar — Koyfin-style compact visualization of a metric's position.

Replaces the old `Peer median: $24B` text caption with a horizontal bar that
shows the watchlist range (min → max), labels the endpoints, and drops a
colored dot at the ticker's position. Direction-aware: for "higher is
better" metrics (ROE, profit margin) the dot greens up on the right; for
"lower is better" (P/E, P/B) it greens up on the left. Neutral metrics
(market cap, beta) render the dot in the accent color.

Implementation is pure HTML/CSS via st.markdown — one `st.plotly_chart` per
metric × ten metrics would hammer page render time.
"""

from __future__ import annotations

from typing import Callable, Optional

import streamlit as st

# Colors match the rest of the theme palette (config/theme.py).
_COLOR_GREEN = "#16A34A"
_COLOR_AMBER = "#F59E0B"
_COLOR_RED = "#DC2626"
_COLOR_NEUTRAL = "#3B82F6"
_COLOR_TRACK = "#2A2E36"
_COLOR_BG = "#0E1117"
_COLOR_MUTED = "#A0A0A0"


def _goodness(value: float, peers: list[float], higher_is_better: Optional[bool]) -> Optional[float]:
    """Return 0.0-1.0 where 1.0 = best.

    None when direction is neutral — the caller then renders the dot in the
    accent color instead of a tiered shade.
    """
    if higher_is_better is None:
        return None
    # Rank within the combined sorted list (including self). Ties use the
    # average rank position so two equal values get the same color.
    combined = sorted(peers + [value])
    # Count strictly-less + half the ties — standard percentile-with-ties.
    lesser = sum(1 for p in combined if p < value)
    equal = sum(1 for p in combined if p == value)
    rank = lesser + (equal - 1) / 2.0
    if len(combined) <= 1:
        return 0.5  # only ourselves → middle of nowhere
    raw = rank / (len(combined) - 1)
    return raw if higher_is_better else (1.0 - raw)


def _dot_color(goodness: Optional[float]) -> str:
    if goodness is None:
        return _COLOR_NEUTRAL
    if goodness >= 0.67:
        return _COLOR_GREEN
    if goodness >= 0.33:
        return _COLOR_AMBER
    return _COLOR_RED


def _position_pct(value: float, peers: list[float]) -> Optional[float]:
    """Position 0.0-1.0 within the min→max range of peers (including self)."""
    all_vals = peers + [value]
    lo, hi = min(all_vals), max(all_vals)
    if hi == lo:
        return None  # degenerate range → no bar to draw
    pos = (value - lo) / (hi - lo)
    return max(0.0, min(1.0, pos))


def peer_rank_bar(
    value: Optional[float],
    peers: list[Optional[float]],
    higher_is_better: Optional[bool] = None,
    format_fn: Optional[Callable[[Optional[float]], str]] = None,
) -> None:
    """Render a compact peer-rank bar under a metric card.

    Args:
        value: The ticker's own value for this metric.
        peers: All OTHER tickers' values (exclude self — caller's responsibility).
        higher_is_better: True (ROE/margin), False (P/E/D/E), None (market cap/beta).
        format_fn: How to render min/max endpoint labels. Defaults to 2-decimal.

    Renders nothing when `value` is None, peers is empty/all-None, or the
    watchlist range is degenerate — no bar is better than a misleading one.
    """
    if value is None:
        return
    present_peers = [p for p in peers if p is not None]
    if not present_peers:
        return
    pos = _position_pct(value, present_peers)
    if pos is None:
        return
    all_vals = present_peers + [value]
    lo, hi = min(all_vals), max(all_vals)
    goodness = _goodness(value, present_peers, higher_is_better)
    dot = _dot_color(goodness)
    fmt = format_fn or (lambda v: f"{v:.2f}" if v is not None else "—")

    html = f"""
    <div style="margin-top: -2px; padding: 0 2px 2px 2px;">
      <div style="position: relative; height: 6px; background: {_COLOR_TRACK}; border-radius: 3px;">
        <div style="position: absolute; left: {pos*100:.1f}%; top: 50%;
                    transform: translate(-50%, -50%);
                    width: 12px; height: 12px; border-radius: 50%;
                    background: {dot}; border: 2px solid {_COLOR_BG};
                    box-shadow: 0 0 0 1px {dot}44;"></div>
      </div>
      <div style="display: flex; justify-content: space-between;
                  font-size: 0.65rem; color: {_COLOR_MUTED}; margin-top: 3px;
                  font-variant-numeric: tabular-nums;">
        <span>{fmt(lo)}</span>
        <span style="font-size: 0.6rem; opacity: 0.7;">peers ({len(present_peers)})</span>
        <span>{fmt(hi)}</span>
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
