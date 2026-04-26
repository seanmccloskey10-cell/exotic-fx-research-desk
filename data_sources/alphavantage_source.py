"""Alpha Vantage data source — tertiary cascade (backup fundamentals).

Free tier: 25 req/day, 5 req/min. Docs: https://www.alphavantage.co/documentation/

Intentionally minimal per PRD §6.5 — pure redundancy. Used only when both
yfinance AND Finnhub have failed. Rate-limit-friendly: one OVERVIEW call
covers both fundamentals and company info.

Not served:
- `get_history` — yfinance is canonical
- `get_news` — 25/day is too tight to be useful as a news feed
- `get_earnings` — Finnhub is canonical
"""

from __future__ import annotations

import logging
import os
from typing import Optional

import requests

from .base import DataSource

log = logging.getLogger(__name__)

SOURCE_NAME = "alphavantage"
BASE_URL = "https://www.alphavantage.co/query"
TIMEOUT_SECONDS = 10


def _safe_float(value) -> Optional[float]:
    if value is None or value == "" or value == "None" or value == "-":
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if v != v:  # NaN
        return None
    return v


def _is_rate_limited(payload: dict) -> bool:
    """AV returns 200 with a 'Note' or 'Information' field when rate-limited."""
    if not isinstance(payload, dict):
        return False
    return bool(payload.get("Note") or payload.get("Information"))


class AlphaVantageSource(DataSource):
    name = SOURCE_NAME

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (api_key or os.getenv("ALPHAVANTAGE_API_KEY") or "").strip()

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _get(self, function: str, extra: Optional[dict] = None) -> Optional[dict]:
        if not self.is_configured():
            return None
        params = {"function": function, "apikey": self.api_key}
        if extra:
            params.update(extra)
        try:
            r = requests.get(BASE_URL, params=params, timeout=TIMEOUT_SECONDS)
        except requests.RequestException as e:
            log.warning("Alpha Vantage %s failed: %s", function, e)
            return None
        if r.status_code != 200:
            log.warning("Alpha Vantage %s returned HTTP %s", function, r.status_code)
            return None
        try:
            payload = r.json()
        except ValueError as e:
            log.warning("Alpha Vantage %s returned non-JSON: %s", function, e)
            return None
        if _is_rate_limited(payload):
            log.warning("Alpha Vantage %s rate-limited: %s", function, payload)
            return None
        return payload

    def get_quote(self, ticker: str) -> Optional[dict]:
        data = self._get("GLOBAL_QUOTE", {"symbol": ticker})
        if not data:
            return None
        q = data.get("Global Quote") or {}
        price = _safe_float(q.get("05. price"))
        if price is None:
            return None
        prev = _safe_float(q.get("08. previous close"))
        change = _safe_float(q.get("09. change"))
        # AV returns change percent as "0.3955%" — strip % then parse.
        raw_pct = q.get("10. change percent")
        change_pct = None
        if isinstance(raw_pct, str):
            change_pct = _safe_float(raw_pct.rstrip("%"))
        return {
            "ticker": ticker,
            "price": price,
            "previous_close": prev,
            "change": change,
            "change_pct": change_pct,
            "day_low": _safe_float(q.get("04. low")),
            "day_high": _safe_float(q.get("03. high")),
            "volume": int(v) if (v := _safe_float(q.get("06. volume"))) else None,
            "avg_volume": None,
            "source": SOURCE_NAME,
        }

    def get_fundamentals(self, ticker: str) -> Optional[dict]:
        data = self._get("OVERVIEW", {"symbol": ticker})
        if not data or not data.get("Symbol"):
            return None
        return {
            "ticker": ticker,
            "market_cap": _safe_float(data.get("MarketCapitalization")),
            "pe_ratio": _safe_float(data.get("PERatio")),
            "pb_ratio": _safe_float(data.get("PriceToBookRatio")),
            "dividend_yield": _safe_float(data.get("DividendYield")),
            "roe": _safe_float(data.get("ReturnOnEquityTTM")),
            "fifty_two_week_high": _safe_float(data.get("52WeekHigh")),
            "fifty_two_week_low": _safe_float(data.get("52WeekLow")),
            "source": SOURCE_NAME,
        }

    def get_company_info(self, ticker: str) -> Optional[dict]:
        data = self._get("OVERVIEW", {"symbol": ticker})
        if not data or not data.get("Symbol"):
            return None
        return {
            "ticker": ticker,
            "name": data.get("Name"),
            "sector": data.get("Sector"),
            "industry": data.get("Industry"),
            "description": data.get("Description"),
            "source": SOURCE_NAME,
        }

    def get_history(self, ticker: str, period: str = "1y", interval: str = "1d"):
        return None
