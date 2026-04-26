"""Derived metrics that turn raw data into insight.

Everything here is pure — takes primitives or already-fetched dicts and
returns numbers. View layer renders; engine layer derives.

What lives here:
- `fifty_two_week_position` — where today's price sits in the 52W range (0-100%)
- `volume_ratio` — today's volume divided by average volume
- `volume_category` — label for the ratio (quiet / normal / heavy / unusual)
- `relative_return` — watchlist ticker's YTD % minus benchmark YTD %
"""

from __future__ import annotations

from typing import Optional

BENCHMARK_SPY = "SPY"  # S&P 500 ETF
BENCHMARK_QQQ = "QQQ"  # Nasdaq-100 ETF


def fifty_two_week_position(
    price: Optional[float],
    low: Optional[float],
    high: Optional[float],
) -> Optional[float]:
    """Return current price's position within [low, high] as 0.0 – 1.0.

    None if any input is missing or the range is degenerate. Values are
    clipped to [0, 1] — a recent break above the 52W high would otherwise
    render as a negative or >1 progress bar.
    """
    if price is None or low is None or high is None:
        return None
    if high <= low:
        return None
    pos = (price - low) / (high - low)
    if pos < 0:
        return 0.0
    if pos > 1:
        return 1.0
    return pos


def volume_ratio(
    today_volume: Optional[int],
    avg_volume: Optional[int],
) -> Optional[float]:
    """Today's volume as a ratio of the running average (1.0 = normal)."""
    if today_volume is None or avg_volume is None or avg_volume <= 0:
        return None
    return float(today_volume) / float(avg_volume)


def volume_category(ratio: Optional[float]) -> str:
    """Human-readable label for the volume-ratio column."""
    if ratio is None:
        return "—"
    if ratio < 0.5:
        return "Quiet"
    if ratio < 1.25:
        return "Normal"
    if ratio < 2.0:
        return "Heavy"
    return "Unusual"


def volume_badge(ratio: Optional[float]) -> str:
    """One-character visual cue. Used in table cells where full label is noisy."""
    if ratio is None:
        return ""
    if ratio < 0.5:
        return "💤"  # sleepy / low volume
    if ratio < 1.25:
        return ""
    if ratio < 2.0:
        return "📊"  # heavy but normal-ish
    return "🔥"  # unusual


def relative_return(ticker_ytd_pct: Optional[float], benchmark_ytd_pct: Optional[float]) -> Optional[float]:
    """Ticker's YTD % minus benchmark's YTD %. Positive = outperforming."""
    if ticker_ytd_pct is None or benchmark_ytd_pct is None:
        return None
    return ticker_ytd_pct - benchmark_ytd_pct
