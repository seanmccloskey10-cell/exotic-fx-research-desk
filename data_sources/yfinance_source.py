"""yfinance data source — primary, no API key required.

Per PRD §13 Phase 1, yfinance is the sole data source at MVP.
Earnings are intentionally NOT served from yfinance (`.earnings_dates` is
unreliable); we surface "Add Finnhub key to unlock" in the UI instead.
"""

from __future__ import annotations

import logging
from typing import Optional

import pandas as pd
import yfinance as yf

from .base import DataSource

log = logging.getLogger(__name__)

SOURCE_NAME = "yfinance"


def _safe(value, cast=None):
    """yfinance .info uses NaN / 0 / None inconsistently. Normalize to None."""
    if value is None:
        return None
    try:
        if isinstance(value, float) and (value != value):  # NaN check
            return None
    except Exception:
        pass
    if cast:
        try:
            return cast(value)
        except (TypeError, ValueError):
            return None
    return value


class YFinanceSource(DataSource):
    name = SOURCE_NAME

    def is_configured(self) -> bool:
        # yfinance needs no key — always available.
        return True

    def _info(self, ticker: str) -> Optional[dict]:
        try:
            return yf.Ticker(ticker).info or None
        except Exception as e:
            log.warning("yfinance .info failed for %s: %s", ticker, e)
            return None

    def get_quote(self, ticker: str) -> Optional[dict]:
        info = self._info(ticker)
        if not info:
            return None
        price = _safe(
            info.get("regularMarketPrice")
            or info.get("currentPrice")
            or info.get("previousClose"),
            float,
        )
        if price is None:
            return None
        prev = _safe(info.get("regularMarketPreviousClose") or info.get("previousClose"), float)
        change = None
        change_pct = None
        if prev is not None and prev != 0:
            change = price - prev
            change_pct = (change / prev) * 100.0
        return {
            "ticker": ticker,
            "price": price,
            "previous_close": prev,
            "change": change,
            "change_pct": change_pct,
            "day_low": _safe(info.get("dayLow") or info.get("regularMarketDayLow"), float),
            "day_high": _safe(info.get("dayHigh") or info.get("regularMarketDayHigh"), float),
            "volume": _safe(info.get("volume") or info.get("regularMarketVolume"), int),
            "avg_volume": _safe(info.get("averageVolume"), int),
            "source": SOURCE_NAME,
        }

    def get_fundamentals(self, ticker: str) -> Optional[dict]:
        info = self._info(ticker)
        if not info:
            return None
        # Normalize dividend yield to a decimal fraction (0.0232 for 2.32%).
        # yfinance 0.2.40+ returns `dividendYield` as PERCENT (e.g. 15.04 for
        # 15.04%, 0.38 for 0.38%). Always /100. `trailingAnnualDividendYield`
        # is a fraction but returns 0 for some tickers (QQQI) where only the
        # forward-looking field is populated — use it as last resort only.
        # Requires yfinance >= 0.2.40 (pinned in requirements.txt).
        dy_raw = _safe(info.get("dividendYield"), float)
        tr_raw = _safe(info.get("trailingAnnualDividendYield"), float)
        div_yield: Optional[float] = None
        if dy_raw is not None and dy_raw > 0:
            div_yield = dy_raw / 100.0
        elif tr_raw is not None and tr_raw > 0:
            div_yield = tr_raw
        # yfinance reports `debtToEquity` as a percent-multiple (e.g. 150 for
        # a 1.5x debt-to-equity ratio). Normalize to the ratio itself so the
        # UI can render "1.5" cleanly alongside other ratios.
        de_raw = _safe(info.get("debtToEquity"), float)
        debt_to_equity = de_raw / 100.0 if de_raw is not None else None
        return {
            "ticker": ticker,
            "market_cap": _safe(info.get("marketCap"), float),
            "pe_ratio": _safe(info.get("trailingPE"), float),
            "forward_pe": _safe(info.get("forwardPE"), float),
            "pb_ratio": _safe(info.get("priceToBook"), float),
            "eps": _safe(info.get("trailingEps"), float),
            "beta": _safe(info.get("beta"), float),
            # `profitMargins` is already a decimal fraction in yfinance.
            "profit_margin": _safe(info.get("profitMargins"), float),
            "debt_to_equity": debt_to_equity,
            "dividend_yield": div_yield,
            "roe": _safe(info.get("returnOnEquity"), float),
            "fifty_two_week_high": _safe(info.get("fiftyTwoWeekHigh"), float),
            "fifty_two_week_low": _safe(info.get("fiftyTwoWeekLow"), float),
            "source": SOURCE_NAME,
        }

    def get_history(
        self, ticker: str, period: str = "1y", interval: str = "1d"
    ) -> Optional[pd.DataFrame]:
        try:
            df = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=False)
            if df is None or df.empty:
                return None
            return df[["Open", "High", "Low", "Close", "Volume"]].copy()
        except Exception as e:
            log.warning("yfinance history failed for %s: %s", ticker, e)
            return None

    def get_company_info(self, ticker: str) -> Optional[dict]:
        info = self._info(ticker)
        if not info:
            return None
        return {
            "ticker": ticker,
            "name": info.get("longName") or info.get("shortName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "description": info.get("longBusinessSummary"),
            "source": SOURCE_NAME,
        }

    # News and earnings are intentionally not implemented here.
    # `get_news` and `get_earnings` inherit the base class None default,
    # so the UI surfaces the "add Finnhub key to unlock" message instead
    # of showing unreliable yfinance data.
