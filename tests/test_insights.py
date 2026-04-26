"""Derived-metrics tests — pure functions, no I/O."""

from __future__ import annotations

from lib.insights import (
    fifty_two_week_position,
    relative_return,
    volume_badge,
    volume_category,
    volume_ratio,
)


# ---------- 52W position ----------

def test_52w_position_mid_range():
    assert fifty_two_week_position(150, 100, 200) == 0.5


def test_52w_position_at_low():
    assert fifty_two_week_position(100, 100, 200) == 0.0


def test_52w_position_at_high():
    assert fifty_two_week_position(200, 100, 200) == 1.0


def test_52w_position_clips_breakout_above():
    """New 52W high — price exceeds stored high. Clip to 1.0 rather than >1."""
    assert fifty_two_week_position(250, 100, 200) == 1.0


def test_52w_position_clips_breakdown_below():
    assert fifty_two_week_position(50, 100, 200) == 0.0


def test_52w_position_none_on_missing():
    assert fifty_two_week_position(None, 100, 200) is None
    assert fifty_two_week_position(150, None, 200) is None
    assert fifty_two_week_position(150, 100, None) is None


def test_52w_position_none_on_degenerate_range():
    """high == low would divide by zero."""
    assert fifty_two_week_position(100, 100, 100) is None


# ---------- Volume ratio + categories ----------

def test_volume_ratio_double():
    assert volume_ratio(2_000_000, 1_000_000) == 2.0


def test_volume_ratio_handles_zero_avg():
    assert volume_ratio(100, 0) is None


def test_volume_ratio_handles_none():
    assert volume_ratio(None, 100) is None
    assert volume_ratio(100, None) is None


def test_volume_category_buckets():
    assert volume_category(0.3) == "Quiet"
    assert volume_category(1.0) == "Normal"
    assert volume_category(1.5) == "Heavy"
    assert volume_category(2.5) == "Unusual"
    assert volume_category(None) == "—"


def test_volume_badge_normal_is_empty():
    assert volume_badge(1.0) == ""


def test_volume_badge_unusual_flags():
    assert volume_badge(3.0) == "🔥"


def test_volume_badge_none_empty():
    assert volume_badge(None) == ""


# ---------- Relative return ----------

def test_relative_return_outperforming():
    # Ticker +15%, SPY +8% → +7% outperformance
    assert relative_return(15.0, 8.0) == 7.0


def test_relative_return_underperforming():
    assert relative_return(3.0, 8.0) == -5.0


def test_relative_return_none_on_missing():
    assert relative_return(None, 8.0) is None
    assert relative_return(8.0, None) is None
