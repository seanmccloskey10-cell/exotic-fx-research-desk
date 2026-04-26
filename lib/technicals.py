"""Technical indicators — pure functions over a close-price series.

Everything here takes a pandas Series / DataFrame and returns primitives or
None. No Streamlit, no I/O, no caching. Views and the briefing engine call
these; tests call them directly with synthetic series.

What lives here:
- `rsi` / `rsi_series` / `rsi_state` — Wilder-smoothed 14-period RSI
- `macd` / `macd_frame` / `macd_state` — 12/26/9 MACD line, signal, histogram + crossover
- `sma` — simple moving average (latest value)
- `price_vs_ma` — current price as a decimal offset from a moving average
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd


# ---------- RSI ----------

def rsi_series(close: pd.Series, period: int = 14) -> Optional[pd.Series]:
    """Full RSI series using Wilder's smoothing (EMA with alpha = 1/period).

    None if there are fewer than `period + 1` observations. Values where the
    recent average loss is zero resolve to 100 (all gains, no losses); values
    where both averages are zero (flat series) remain NaN.
    """
    if close is None or len(close) < period + 1:
        return None
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    # avg_loss == 0 but avg_gain > 0 → all-gain regime, RSI is 100
    all_gain = (avg_loss == 0) & (avg_gain > 0)
    rsi = rsi.where(~all_gain, 100.0)
    return rsi


def rsi(close: pd.Series, period: int = 14) -> Optional[float]:
    """Latest RSI value. None if insufficient data or undefined (flat series)."""
    series = rsi_series(close, period)
    if series is None or series.empty:
        return None
    val = series.iloc[-1]
    if pd.isna(val):
        return None
    return float(val)


def rsi_state(value: Optional[float]) -> str:
    """Human-readable label for the RSI current value.

    Convention: ≥70 overbought, ≤30 oversold, else neutral.
    """
    if value is None:
        return "Insufficient data"
    if value >= 70:
        return "Overbought"
    if value <= 30:
        return "Oversold"
    return "Neutral"


# ---------- MACD ----------

def macd_frame(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> Optional[pd.DataFrame]:
    """Full MACD frame — columns `[macd, signal, histogram]`.

    None if fewer than `slow + signal` observations (EMAs would be
    meaningless over shorter windows).
    """
    if close is None or len(close) < slow + signal:
        return None
    fast_ema = close.ewm(span=fast, adjust=False).mean()
    slow_ema = close.ewm(span=slow, adjust=False).mean()
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return pd.DataFrame(
        {"macd": macd_line, "signal": signal_line, "histogram": histogram}
    )


def macd(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> Optional[dict]:
    """Latest MACD values as a dict: `{macd, signal, histogram}`. None if insufficient data."""
    frame = macd_frame(close, fast, slow, signal)
    if frame is None or frame.empty:
        return None
    last = frame.iloc[-1]
    if last.isna().any():
        return None
    return {
        "macd": float(last["macd"]),
        "signal": float(last["signal"]),
        "histogram": float(last["histogram"]),
    }


def macd_state(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> dict:
    """Most recent MACD/signal crossover.

    Returns `{"crossover": "bullish"|"bearish"|"none", "days_since_crossover": int|None}`.
    "bullish" = histogram crossed from negative to positive (MACD moved above signal).
    Day count is in bars (trading days for daily data).
    """
    frame = macd_frame(close, fast, slow, signal)
    if frame is None or len(frame) < 2:
        return {"crossover": "none", "days_since_crossover": None}
    hist = frame["histogram"]
    # Sign of histogram: +1 above signal, -1 below, 0 exactly on it
    signs = np.sign(hist.fillna(0)).astype(int)
    # Scan backwards for the most recent non-zero sign flip
    for i in range(len(signs) - 1, 0, -1):
        curr = signs.iloc[i]
        prev = signs.iloc[i - 1]
        if curr != 0 and prev != 0 and curr != prev:
            days_since = len(signs) - 1 - i
            return {
                "crossover": "bullish" if curr > 0 else "bearish",
                "days_since_crossover": int(days_since),
            }
    return {"crossover": "none", "days_since_crossover": None}


# ---------- Moving averages ----------

def sma(close: pd.Series, window: int) -> Optional[float]:
    """Latest simple moving average. None if fewer than `window` observations."""
    if close is None or len(close) < window:
        return None
    val = close.rolling(window).mean().iloc[-1]
    if pd.isna(val):
        return None
    return float(val)


def price_vs_ma(price: Optional[float], ma: Optional[float]) -> Optional[float]:
    """Price as a decimal offset from a moving average.

    `0.05` = price is 5% above the MA. None if either input is missing or the
    MA is zero.
    """
    if price is None or ma is None or ma == 0:
        return None
    return (price / ma) - 1.0
