"""Technical-indicator tests — pure functions, synthetic series, no I/O."""

from __future__ import annotations

import numpy as np
import pandas as pd

from lib.technicals import (
    macd,
    macd_frame,
    macd_state,
    price_vs_ma,
    rsi,
    rsi_series,
    rsi_state,
    sma,
)


def _rising(n: int = 60, start: float = 100.0, step: float = 1.0) -> pd.Series:
    return pd.Series([start + i * step for i in range(n)])


def _falling(n: int = 60, start: float = 200.0, step: float = 1.0) -> pd.Series:
    return pd.Series([start - i * step for i in range(n)])


def _flat(n: int = 60, value: float = 100.0) -> pd.Series:
    return pd.Series([value] * n)


def _alternating(n: int = 60, base: float = 100.0, delta: float = 1.0) -> pd.Series:
    return pd.Series([base + (delta if i % 2 else -delta) for i in range(n)])


# ---------- RSI ----------

def test_rsi_rising_series_approaches_100():
    val = rsi(_rising(), period=14)
    assert val is not None
    assert val > 99.0


def test_rsi_falling_series_approaches_0():
    val = rsi(_falling(), period=14)
    assert val is not None
    assert val < 1.0


def test_rsi_alternating_series_around_50():
    # Equal average gain and loss → RSI ~50
    val = rsi(_alternating(), period=14)
    assert val is not None
    assert 45.0 <= val <= 55.0


def test_rsi_flat_series_is_none():
    # Both avg_gain and avg_loss are 0 → RSI undefined
    assert rsi(_flat(), period=14) is None


def test_rsi_insufficient_data_is_none():
    # Need at least period + 1 candles
    short = pd.Series([100.0] * 10)
    assert rsi(short, period=14) is None


def test_rsi_series_returns_full_length():
    s = rsi_series(_rising(60), period=14)
    assert s is not None
    assert len(s) == 60


def test_rsi_state_labels_at_boundaries():
    assert rsi_state(None) == "Insufficient data"
    assert rsi_state(29.9) == "Oversold"
    assert rsi_state(30.0) == "Oversold"
    assert rsi_state(30.1) == "Neutral"
    assert rsi_state(69.9) == "Neutral"
    assert rsi_state(70.0) == "Overbought"
    assert rsi_state(85.0) == "Overbought"


# ---------- MACD ----------

def test_macd_flat_series_is_all_zero():
    m = macd(_flat(100), fast=12, slow=26, signal=9)
    assert m is not None
    assert abs(m["macd"]) < 1e-9
    assert abs(m["signal"]) < 1e-9
    assert abs(m["histogram"]) < 1e-9


def test_macd_insufficient_data_is_none():
    short = pd.Series([100.0] * 30)  # need ≥ 26 + 9 = 35
    assert macd(short) is None


def test_macd_rising_series_is_bullish():
    # Fast EMA > slow EMA in a rising series → positive MACD line
    m = macd(_rising(100))
    assert m is not None
    assert m["macd"] > 0


def test_macd_frame_shape():
    frame = macd_frame(_rising(100))
    assert frame is not None
    assert list(frame.columns) == ["macd", "signal", "histogram"]
    assert len(frame) == 100


def test_macd_state_flat_series_no_crossover():
    state = macd_state(_flat(100))
    assert state == {"crossover": "none", "days_since_crossover": None}


def test_macd_state_detects_recent_flip():
    # Construct a series that rises then falls: should produce a bearish crossover
    # late in the series.
    rising = np.linspace(100, 200, 60)
    falling = np.linspace(200, 150, 40)
    series = pd.Series(np.concatenate([rising, falling]))
    state = macd_state(series)
    assert state["crossover"] in ("bullish", "bearish")
    assert state["days_since_crossover"] is not None
    assert state["days_since_crossover"] >= 0


# ---------- SMA ----------

def test_sma_matches_rolling_mean():
    s = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
    assert sma(s, window=3) == 40.0  # mean(30, 40, 50)


def test_sma_insufficient_data_is_none():
    s = pd.Series([1.0, 2.0])
    assert sma(s, window=5) is None


def test_sma_full_window_matches_pandas():
    s = _rising(50)
    expected = s.rolling(20).mean().iloc[-1]
    assert sma(s, window=20) == float(expected)


# ---------- Price vs MA ----------

def test_price_vs_ma_above():
    assert abs(price_vs_ma(110.0, 100.0) - 0.1) < 1e-9


def test_price_vs_ma_below():
    # 90 / 100 - 1 = -0.1
    assert abs(price_vs_ma(90.0, 100.0) - (-0.1)) < 1e-9


def test_price_vs_ma_none_on_missing():
    assert price_vs_ma(None, 100.0) is None
    assert price_vs_ma(100.0, None) is None


def test_price_vs_ma_zero_ma_is_none():
    assert price_vs_ma(100.0, 0) is None
