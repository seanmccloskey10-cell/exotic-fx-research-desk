"""Peer-rank bar tests — exercise the pure percentile/position math.

The HTML rendering is cosmetic and hard to assert on cleanly; the logic
that decides the color and bar position is what would silently regress.
"""

from __future__ import annotations

from components.peer_rank_bar import (
    _COLOR_AMBER,
    _COLOR_GREEN,
    _COLOR_NEUTRAL,
    _COLOR_RED,
    _dot_color,
    _goodness,
    _position_pct,
)


# ---------- _position_pct ----------

def test_position_pct_middle():
    # Value 15 in range [10, 20] → 0.5
    assert _position_pct(15.0, [10.0, 20.0]) == 0.5


def test_position_pct_at_min():
    assert _position_pct(10.0, [15.0, 20.0]) == 0.0


def test_position_pct_at_max():
    assert _position_pct(25.0, [10.0, 15.0]) == 1.0


def test_position_pct_degenerate_range_returns_none():
    # All values equal → no range to plot
    assert _position_pct(10.0, [10.0, 10.0]) is None


def test_position_pct_clips_below_min():
    # Shouldn't happen in practice (caller sets the range), but guard anyway.
    assert _position_pct(0.0, [5.0, 10.0, 15.0]) == 0.0


# ---------- _goodness ----------

def test_goodness_neutral_returns_none():
    assert _goodness(15.0, [10.0, 20.0], higher_is_better=None) is None


def test_goodness_higher_is_better_highest_value():
    # ROE of 0.40 vs peers [0.10, 0.20, 0.30] → best → 1.0
    g = _goodness(0.40, [0.10, 0.20, 0.30], higher_is_better=True)
    assert g == 1.0


def test_goodness_higher_is_better_lowest_value():
    g = _goodness(0.05, [0.10, 0.20, 0.30], higher_is_better=True)
    assert g == 0.0


def test_goodness_lower_is_better_lowest_value():
    # P/E of 8 vs peers [18, 24, 35] → lowest → best for value → 1.0
    g = _goodness(8.0, [18.0, 24.0, 35.0], higher_is_better=False)
    assert g == 1.0


def test_goodness_lower_is_better_highest_value():
    g = _goodness(50.0, [18.0, 24.0, 35.0], higher_is_better=False)
    assert g == 0.0


def test_goodness_middle_rank_around_half():
    # Middle of a 4-value list (self + 3 peers) → roughly 0.5
    g = _goodness(20.0, [10.0, 15.0, 30.0], higher_is_better=True)
    # Combined sorted: [10, 15, 20, 30], self is index 2 of 4 → 2/3 ≈ 0.666
    assert abs(g - 2 / 3) < 1e-6


# ---------- _dot_color ----------

def test_dot_color_green_threshold():
    assert _dot_color(0.67) == _COLOR_GREEN
    assert _dot_color(1.0) == _COLOR_GREEN


def test_dot_color_amber_middle():
    assert _dot_color(0.5) == _COLOR_AMBER
    assert _dot_color(0.34) == _COLOR_AMBER


def test_dot_color_red_threshold():
    assert _dot_color(0.32) == _COLOR_RED
    assert _dot_color(0.0) == _COLOR_RED


def test_dot_color_neutral_when_direction_unknown():
    assert _dot_color(None) == _COLOR_NEUTRAL
