"""Finnhub source tests — mocked HTTP, no network.

Verifies the shape-parsing, not Finnhub's actual behavior. Every endpoint
response is canned; tests confirm our parser produces the documented
`DataSource` return shapes.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

import pytest

from data_sources import finnhub_source
from data_sources.finnhub_source import FinnhubSource


class _FakeResponse:
    def __init__(self, status_code: int = 200, json_data=None):
        self.status_code = status_code
        self._json = json_data

    def json(self):
        return self._json


def _mock_get(json_data, status_code: int = 200):
    def _inner(*args, **kwargs):
        return _FakeResponse(status_code=status_code, json_data=json_data)
    return _inner


def test_not_configured_without_key(monkeypatch):
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
    src = FinnhubSource()
    assert src.is_configured() is False
    assert src.get_quote("AAPL") is None
    assert src.get_news("AAPL") is None


def test_configured_with_key():
    src = FinnhubSource(api_key="test123")
    assert src.is_configured() is True


def test_get_quote_parses_canonical_shape():
    src = FinnhubSource(api_key="test123")
    canned = {"c": 261.74, "h": 263.31, "l": 260.68, "o": 261.07, "pc": 259.45, "d": 2.29, "dp": 0.88}
    with patch.object(finnhub_source.requests, "get", side_effect=_mock_get(canned)):
        q = src.get_quote("AAPL")
    assert q is not None
    assert q["ticker"] == "AAPL"
    assert q["price"] == 261.74
    assert q["previous_close"] == 259.45
    assert q["change"] == 2.29
    assert q["change_pct"] == 0.88
    assert q["day_low"] == 260.68
    assert q["day_high"] == 263.31
    assert q["source"] == "finnhub"


def test_get_quote_none_when_price_zero():
    """Finnhub returns c=0 for unknown tickers — we treat that as not-found."""
    src = FinnhubSource(api_key="test123")
    canned = {"c": 0, "pc": 0, "d": 0, "dp": 0}
    with patch.object(finnhub_source.requests, "get", side_effect=_mock_get(canned)):
        assert src.get_quote("XXXX") is None


def test_get_quote_none_on_http_error():
    src = FinnhubSource(api_key="test123")
    with patch.object(finnhub_source.requests, "get", side_effect=_mock_get({}, status_code=429)):
        assert src.get_quote("AAPL") is None


def test_get_fundamentals_parses_metric_envelope():
    src = FinnhubSource(api_key="test123")
    # Finnhub convention: marketCap in millions; roeTTM as percent; dividend
    # yield as decimal fraction. Parser must normalize to raw USD + decimal
    # fractions to match yfinance / Alpha Vantage.
    canned = {
        "metric": {
            "marketCapitalization": 1_415_993,   # 1.416T USD, expressed in millions
            "peBasicExclExtraTTM": 29.45,
            "pbAnnual": 35.18,
            "dividendYieldIndicatedAnnual": 0.0058,  # already a fraction
            "roeTTM": 23.45,                     # percent per Finnhub docs
            "52WeekHigh": 264.01,
            "52WeekLow": 124.17,
        },
        "metricType": "all",
    }
    with patch.object(finnhub_source.requests, "get", side_effect=_mock_get(canned)):
        f = src.get_fundamentals("AAPL")
    assert f is not None
    assert f["market_cap"] == 1_415_993 * 1_000_000  # 1.416T USD
    assert f["pe_ratio"] == 29.45
    assert f["pb_ratio"] == 35.18
    assert f["dividend_yield"] == 0.0058
    assert f["roe"] == pytest.approx(0.2345)  # 23.45% → 0.2345 fraction
    assert f["fifty_two_week_high"] == 264.01
    assert f["fifty_two_week_low"] == 124.17


def test_get_company_info_parses_profile():
    src = FinnhubSource(api_key="test123")
    canned = {
        "name": "Apple Inc",
        "finnhubIndustry": "Technology",
        "ticker": "AAPL",
    }
    with patch.object(finnhub_source.requests, "get", side_effect=_mock_get(canned)):
        info = src.get_company_info("AAPL")
    assert info is not None
    assert info["name"] == "Apple Inc"
    assert info["sector"] == "Technology"
    assert info["source"] == "finnhub"


def test_get_news_caps_at_ten_articles():
    src = FinnhubSource(api_key="test123")
    articles = [
        {
            "datetime": 1700000000 + i,
            "headline": f"Headline {i}",
            "url": f"https://example.com/{i}",
            "source": "Reuters",
            "summary": "Body.",
        }
        for i in range(20)
    ]
    with patch.object(finnhub_source.requests, "get", side_effect=_mock_get(articles)):
        news = src.get_news("AAPL")
    assert news is not None
    assert len(news) == 10
    first = news[0]
    assert first["title"] == "Headline 0"
    assert first["url"] == "https://example.com/0"
    assert first["publisher"] == "Reuters"
    assert isinstance(first["published_at"], datetime)
    assert first["source"] == "finnhub"


def test_get_news_skips_items_missing_required_fields():
    src = FinnhubSource(api_key="test123")
    articles = [
        {"datetime": 1700000000, "headline": "OK", "url": "http://x"},
        {"datetime": 1700000000, "headline": "", "url": "http://y"},  # no title
        {"datetime": 1700000000, "headline": "No URL"},
    ]
    with patch.object(finnhub_source.requests, "get", side_effect=_mock_get(articles)):
        news = src.get_news("AAPL")
    assert news is not None
    assert len(news) == 1


def test_get_news_none_when_empty():
    src = FinnhubSource(api_key="test123")
    with patch.object(finnhub_source.requests, "get", side_effect=_mock_get([])):
        assert src.get_news("AAPL") is None


def test_get_earnings_picks_earliest_future_event():
    src = FinnhubSource(api_key="test123")
    canned = {
        "earningsCalendar": [
            {"date": "2026-07-15", "symbol": "AAPL", "epsEstimate": 1.50, "hour": "amc"},
            {"date": "2026-05-01", "symbol": "AAPL", "epsEstimate": 1.25, "hour": "bmo"},
            {"date": "2026-10-20", "symbol": "AAPL", "epsEstimate": 1.75, "hour": "amc"},
        ]
    }
    with patch.object(finnhub_source.requests, "get", side_effect=_mock_get(canned)):
        e = src.get_earnings("AAPL")
    assert e is not None
    assert str(e["next_date"]) == "2026-05-01"
    assert e["eps_estimate"] == 1.25
    assert e["time"] == "bmo"


def test_get_history_always_none():
    """Finnhub candle endpoint is paid-tier — source explicitly returns None."""
    src = FinnhubSource(api_key="test123")
    assert src.get_history("AAPL") is None
