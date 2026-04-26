"""Finnhub data source — secondary cascade.

Free tier: 60 req/min. Docs: https://finnhub.io/docs/api

What this source serves (Phase 3):
- `get_quote` — /quote
- `get_fundamentals` — /stock/metric?metric=all
- `get_company_info` — /stock/profile2
- `get_news` — /company-news (last 7 days)
- `get_earnings` — /calendar/earnings (next 60 days)

Not served:
- `get_history` — candle endpoint is paid-tier only. yfinance stays canonical.

Errors / timeouts / missing fields return None so the orchestrator cascades
cleanly. The UI surfaces "Add Finnhub key to unlock" when this source is
unconfigured.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests

from .base import DataSource

log = logging.getLogger(__name__)

SOURCE_NAME = "finnhub"
BASE_URL = "https://finnhub.io/api/v1"
TIMEOUT_SECONDS = 10


def _safe_float(value) -> Optional[float]:
    if value is None:
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if v != v:  # NaN
        return None
    return v


class FinnhubSource(DataSource):
    name = SOURCE_NAME

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (api_key or os.getenv("FINNHUB_API_KEY") or "").strip()

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _get(self, path: str, params: Optional[dict] = None) -> Optional[dict]:
        if not self.is_configured():
            return None
        params = dict(params or {})
        params["token"] = self.api_key
        try:
            r = requests.get(f"{BASE_URL}{path}", params=params, timeout=TIMEOUT_SECONDS)
        except requests.RequestException as e:
            log.warning("Finnhub %s failed: %s", path, e)
            return None
        if r.status_code != 200:
            log.warning("Finnhub %s returned HTTP %s", path, r.status_code)
            return None
        try:
            return r.json()
        except ValueError as e:
            log.warning("Finnhub %s returned non-JSON: %s", path, e)
            return None

    def get_quote(self, ticker: str) -> Optional[dict]:
        data = self._get("/quote", {"symbol": ticker})
        if not data:
            return None
        price = _safe_float(data.get("c"))
        if price is None or price == 0:
            # Finnhub returns c=0 when the symbol is unknown.
            return None
        prev = _safe_float(data.get("pc"))
        change = _safe_float(data.get("d"))
        change_pct = _safe_float(data.get("dp"))
        if change is None and prev is not None:
            change = price - prev
        if change_pct is None and prev:
            change_pct = (change / prev) * 100.0 if change is not None else None
        return {
            "ticker": ticker,
            "price": price,
            "previous_close": prev,
            "change": change,
            "change_pct": change_pct,
            "day_low": _safe_float(data.get("l")),
            "day_high": _safe_float(data.get("h")),
            "volume": None,
            "avg_volume": None,
            "source": SOURCE_NAME,
        }

    def get_fundamentals(self, ticker: str) -> Optional[dict]:
        data = self._get("/stock/metric", {"symbol": ticker, "metric": "all"})
        if not data:
            return None
        m = data.get("metric") or {}
        if not m:
            return None
        # Finnhub returns `marketCapitalization` in MILLIONS of the listed
        # currency. Convert to raw units so it's consistent with yfinance
        # (raw USD) and Alpha Vantage (raw USD).
        raw_mc = _safe_float(m.get("marketCapitalization"))
        market_cap = raw_mc * 1_000_000.0 if raw_mc is not None else None
        # ROE from Finnhub is returned as a percent (e.g. 23.45 = 23.45%);
        # convert to decimal fraction to match the normalized shape.
        raw_roe = _safe_float(m.get("roeTTM"))
        roe = raw_roe / 100.0 if raw_roe is not None else None
        return {
            "ticker": ticker,
            "market_cap": market_cap,
            "pe_ratio": _safe_float(m.get("peBasicExclExtraTTM") or m.get("peTTM")),
            "pb_ratio": _safe_float(m.get("pbAnnual") or m.get("pbQuarterly")),
            "dividend_yield": _safe_float(m.get("dividendYieldIndicatedAnnual")),
            "roe": roe,
            "fifty_two_week_high": _safe_float(m.get("52WeekHigh")),
            "fifty_two_week_low": _safe_float(m.get("52WeekLow")),
            "source": SOURCE_NAME,
        }

    def get_company_info(self, ticker: str) -> Optional[dict]:
        data = self._get("/stock/profile2", {"symbol": ticker})
        if not data or not data.get("name"):
            return None
        return {
            "ticker": ticker,
            "name": data.get("name"),
            "sector": data.get("finnhubIndustry"),  # Finnhub uses "industry" as broad sector
            "industry": data.get("finnhubIndustry"),
            "description": None,  # /profile2 doesn't include a description
            "source": SOURCE_NAME,
        }

    def get_history(self, ticker: str, period: str = "1y", interval: str = "1d"):
        # Candle endpoint is paid-tier only. Let yfinance stay canonical.
        return None

    def get_news(self, ticker: str) -> Optional[list]:
        today = datetime.now(timezone.utc).date()
        week_ago = today - timedelta(days=7)
        data = self._get(
            "/company-news",
            {
                "symbol": ticker,
                "from": week_ago.isoformat(),
                "to": today.isoformat(),
            },
        )
        if not isinstance(data, list) or not data:
            return None
        articles: list[dict] = []
        for item in data[:10]:  # cap at 10
            ts = item.get("datetime")
            published_at = None
            if isinstance(ts, (int, float)) and ts > 0:
                try:
                    published_at = datetime.fromtimestamp(int(ts), tz=timezone.utc)
                except (OSError, ValueError):
                    published_at = None
            title = item.get("headline")
            url = item.get("url")
            if not (title and url):
                continue
            articles.append(
                {
                    "title": title,
                    "url": url,
                    "publisher": item.get("source"),
                    "published_at": published_at,
                    "summary": item.get("summary") or None,
                    "source": SOURCE_NAME,
                }
            )
        return articles or None

    def get_earnings(self, ticker: str) -> Optional[dict]:
        today = datetime.now(timezone.utc).date()
        horizon = today + timedelta(days=90)
        data = self._get(
            "/calendar/earnings",
            {"symbol": ticker, "from": today.isoformat(), "to": horizon.isoformat()},
        )
        if not data:
            return None
        events = data.get("earningsCalendar") or []
        if not events:
            return None
        # Earliest future event.
        def _event_date(e):
            try:
                return datetime.fromisoformat(e.get("date", ""))
            except (TypeError, ValueError):
                return datetime.max

        events = sorted(events, key=_event_date)
        nxt = events[0]
        try:
            nxt_date = datetime.fromisoformat(nxt.get("date", "")).date()
        except (TypeError, ValueError):
            nxt_date = None
        return {
            "ticker": ticker,
            "next_date": nxt_date,
            "eps_estimate": _safe_float(nxt.get("epsEstimate")),
            "revenue_estimate": _safe_float(nxt.get("revenueEstimate")),
            "time": nxt.get("hour"),  # "bmo" / "amc" / None
            "source": SOURCE_NAME,
        }
