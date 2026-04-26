"""Abstract base for data sources.

Every source (yfinance, Finnhub, Alpha Vantage, ...) implements this interface.
The orchestrator cascades across sources in priority order — first non-None
result wins. A source that isn't configured (e.g. missing API key) returns
False from `is_configured()` and is skipped by the orchestrator.

Return shapes are normalized (see docstrings per method) so views never need
to know which source produced a value.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

import pandas as pd


class DataSource(ABC):
    name: str = "base"

    @abstractmethod
    def is_configured(self) -> bool:
        """True when this source is ready to serve requests (keys present, etc.)."""

    @abstractmethod
    def get_quote(self, ticker: str) -> Optional[dict]:
        """Return current quote or None on failure.

        Shape:
            {
                "ticker": str,
                "price": float,
                "previous_close": float | None,
                "change": float | None,       # absolute $ change
                "change_pct": float | None,   # percent, e.g. 1.78 means +1.78%
                "day_low": float | None,
                "day_high": float | None,
                "volume": int | None,
                "avg_volume": int | None,
                "source": str,
            }
        """

    @abstractmethod
    def get_fundamentals(self, ticker: str) -> Optional[dict]:
        """Return fundamentals or None on failure.

        Shape:
            {
                "ticker": str,
                "market_cap": float | None,
                "pe_ratio": float | None,           # trailing PE
                "forward_pe": float | None,         # forward PE (None if unavailable)
                "pb_ratio": float | None,
                "eps": float | None,                # trailing EPS in $ per share
                "beta": float | None,               # 5Y monthly beta vs market
                "profit_margin": float | None,      # decimal, 0.23 = 23%
                "debt_to_equity": float | None,     # ratio, 1.5 = 1.5x equity in debt
                "dividend_yield": float | None,     # decimal, 0.025 = 2.5%
                "roe": float | None,                # decimal, 0.15 = 15%
                "fifty_two_week_high": float | None,
                "fifty_two_week_low": float | None,
                "source": str,
            }

        Sources that can't populate a field should return None for it —
        views render missing values as em-dashes rather than branching
        on which source produced the dict.
        """

    @abstractmethod
    def get_history(
        self, ticker: str, period: str = "1y", interval: str = "1d"
    ) -> Optional[pd.DataFrame]:
        """Return OHLCV DataFrame indexed by date or None on failure.

        Columns: Open, High, Low, Close, Volume.
        """

    @abstractmethod
    def get_company_info(self, ticker: str) -> Optional[dict]:
        """Return company metadata or None on failure.

        Shape:
            {
                "ticker": str,
                "name": str | None,
                "sector": str | None,
                "industry": str | None,
                "description": str | None,
                "source": str,
            }
        """

    def get_news(self, ticker: str) -> Optional[list[dict]]:
        """Return recent news or None.

        Each article shape:
            {
                "title": str,
                "url": str,
                "publisher": str | None,    # e.g. "Reuters", "Bloomberg"
                "published_at": datetime | None,
                "summary": str | None,      # plain text, no HTML
                "source": str,              # which DataSource produced this
            }

        Default: not supported by this source.
        """
        return None

    def get_earnings(self, ticker: str) -> Optional[dict]:
        """Return upcoming earnings info or None.

        Shape:
            {
                "ticker": str,
                "next_date": date | None,
                "eps_estimate": float | None,
                "revenue_estimate": float | None,
                "time": str | None,        # "bmo" / "amc" / None
                "source": str,
            }

        Default: not supported.
        """
        return None
