"""Data orchestrator — cascades calls across sources in priority order.

Usage:
    orch = build_default_orchestrator()
    quote = orch.get_quote("CRDO")   # tries yfinance first, then Finnhub, ...

Design:
- Only sources returning True from `is_configured()` are consulted.
- First non-None result wins.
- Any exception from a source is logged and the cascade continues.
- If every source fails, returns None and lets the caller render a
  "Data unavailable" state.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, List, Optional

import pandas as pd

from .base import DataSource

log = logging.getLogger(__name__)


class DataOrchestrator:
    def __init__(self, sources: List[DataSource]):
        self.all_sources = sources
        self.active_sources = [s for s in sources if s.is_configured()]
        log.info(
            "DataOrchestrator initialized: active=%s inactive=%s",
            [s.name for s in self.active_sources],
            [s.name for s in sources if not s.is_configured()],
        )

    def _cascade(self, method: str, *args, **kwargs) -> Any:
        for source in self.active_sources:
            try:
                fn: Callable = getattr(source, method)
                result = fn(*args, **kwargs)
                if result is not None:
                    return result
            except Exception as e:
                log.warning(
                    "Source %s failed on %s(%s): %s", source.name, method, args, e
                )
                continue
        return None

    def get_quote(self, ticker: str) -> Optional[dict]:
        return self._cascade("get_quote", ticker)

    def get_fundamentals(self, ticker: str) -> Optional[dict]:
        return self._cascade("get_fundamentals", ticker)

    def get_history(
        self, ticker: str, period: str = "1y", interval: str = "1d"
    ) -> Optional[pd.DataFrame]:
        return self._cascade("get_history", ticker, period, interval)

    def get_company_info(self, ticker: str) -> Optional[dict]:
        return self._cascade("get_company_info", ticker)

    def get_news(self, ticker: str) -> Optional[list]:
        return self._cascade("get_news", ticker)

    def get_earnings(self, ticker: str) -> Optional[dict]:
        return self._cascade("get_earnings", ticker)

    def status(self) -> list[dict]:
        """Return per-source availability for the sidebar data-source indicator."""
        return [
            {"name": s.name, "active": s.is_configured()}
            for s in self.all_sources
        ]


def build_default_orchestrator() -> DataOrchestrator:
    """Default cascade order: yfinance → Finnhub → Alpha Vantage.

    Sources are lazy-imported here so unit tests that use fake sources do
    not need yfinance / requests / etc. installed just to import the
    orchestrator class.
    """
    from .alphavantage_source import AlphaVantageSource
    from .finnhub_source import FinnhubSource
    from .yfinance_source import YFinanceSource

    return DataOrchestrator(
        [
            YFinanceSource(),
            FinnhubSource(),
            AlphaVantageSource(),
        ]
    )
