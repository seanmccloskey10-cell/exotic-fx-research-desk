"""Shared timeframe definitions for charts.

Keeps Overview, Detail, Comparison, and any future views aligned on what
"1M" / "1Y" etc. actually mean for yfinance period + interval pairs.

Intraday (1D / 5D) uses sub-daily intervals; all others use daily or
weekly bars. Values match yfinance's accepted period/interval combinations.
"""

from __future__ import annotations

from collections import OrderedDict

# label -> (period, interval)
TIMEFRAMES: "OrderedDict[str, tuple[str, str]]" = OrderedDict(
    [
        ("1D", ("1d", "5m")),
        ("5D", ("5d", "30m")),
        ("1M", ("1mo", "1d")),
        ("3M", ("3mo", "1d")),
        ("6M", ("6mo", "1d")),
        ("1Y", ("1y", "1d")),
        ("5Y", ("5y", "1wk")),
    ]
)

DEFAULT_TIMEFRAME = "1Y"
DEFAULT_INDEX = list(TIMEFRAMES.keys()).index(DEFAULT_TIMEFRAME)

# Sparkline on the overview row — 1 month of daily bars.
SPARKLINE_PERIOD = "1mo"
SPARKLINE_INTERVAL = "1d"
