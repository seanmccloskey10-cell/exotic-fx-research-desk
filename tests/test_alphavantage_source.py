"""Alpha Vantage source tests — mocked HTTP, no network.

Verifies parser shapes. AV's rate-limit response (HTTP 200 + "Note"/
"Information" field in JSON) is covered explicitly — it MUST return None
so the orchestrator cascade moves on rather than surfacing garbage.
"""

from __future__ import annotations

from unittest.mock import patch

from data_sources import alphavantage_source
from data_sources.alphavantage_source import AlphaVantageSource


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
    monkeypatch.delenv("ALPHAVANTAGE_API_KEY", raising=False)
    src = AlphaVantageSource()
    assert src.is_configured() is False
    assert src.get_quote("IBM") is None


def test_configured_with_key():
    src = AlphaVantageSource(api_key="demo")
    assert src.is_configured() is True


def test_get_quote_parses_global_quote():
    src = AlphaVantageSource(api_key="demo")
    canned = {
        "Global Quote": {
            "01. symbol": "IBM",
            "02. open": "127.1600",
            "03. high": "127.6500",
            "04. low": "126.7200",
            "05. price": "126.9300",
            "06. volume": "3017447",
            "07. latest trading day": "2023-12-08",
            "08. previous close": "126.4300",
            "09. change": "0.5000",
            "10. change percent": "0.3955%",
        }
    }
    with patch.object(alphavantage_source.requests, "get", side_effect=_mock_get(canned)):
        q = src.get_quote("IBM")
    assert q is not None
    assert q["price"] == 126.93
    assert q["previous_close"] == 126.43
    assert q["change"] == 0.50
    assert q["change_pct"] == 0.3955
    assert q["day_low"] == 126.72
    assert q["day_high"] == 127.65
    assert q["volume"] == 3017447
    assert q["source"] == "alphavantage"


def test_get_quote_none_on_rate_limit():
    src = AlphaVantageSource(api_key="demo")
    canned = {"Note": "Thank you for using Alpha Vantage! Our standard API call frequency is..."}
    with patch.object(alphavantage_source.requests, "get", side_effect=_mock_get(canned)):
        assert src.get_quote("IBM") is None


def test_get_quote_none_on_information_field():
    """Recent AV versions use 'Information' instead of 'Note' for the limit message."""
    src = AlphaVantageSource(api_key="demo")
    canned = {"Information": "We have detected your API key and will provide..."}
    with patch.object(alphavantage_source.requests, "get", side_effect=_mock_get(canned)):
        assert src.get_quote("IBM") is None


def test_get_quote_none_on_empty_envelope():
    src = AlphaVantageSource(api_key="demo")
    with patch.object(alphavantage_source.requests, "get", side_effect=_mock_get({"Global Quote": {}})):
        assert src.get_quote("IBM") is None


def test_get_fundamentals_parses_overview():
    src = AlphaVantageSource(api_key="demo")
    canned = {
        "Symbol": "IBM",
        "Name": "International Business Machines",
        "MarketCapitalization": "169987043328",
        "PERatio": "20.5",
        "PriceToBookRatio": "7.27",
        "DividendYield": "0.032",
        "ReturnOnEquityTTM": "0.405",
        "52WeekHigh": "169.65",
        "52WeekLow": "120.55",
    }
    with patch.object(alphavantage_source.requests, "get", side_effect=_mock_get(canned)):
        f = src.get_fundamentals("IBM")
    assert f is not None
    assert f["market_cap"] == 169987043328
    assert f["pe_ratio"] == 20.5
    assert f["pb_ratio"] == 7.27
    assert f["dividend_yield"] == 0.032
    assert f["roe"] == 0.405


def test_get_fundamentals_treats_dash_as_none():
    """AV writes '-' or 'None' for missing fields — parser must coerce to None."""
    src = AlphaVantageSource(api_key="demo")
    canned = {
        "Symbol": "IBM",
        "MarketCapitalization": "-",
        "PERatio": "None",
        "PriceToBookRatio": "",
        "DividendYield": "0.032",
        "ReturnOnEquityTTM": "0.405",
        "52WeekHigh": "169.65",
        "52WeekLow": "120.55",
    }
    with patch.object(alphavantage_source.requests, "get", side_effect=_mock_get(canned)):
        f = src.get_fundamentals("IBM")
    assert f is not None
    assert f["market_cap"] is None
    assert f["pe_ratio"] is None
    assert f["pb_ratio"] is None
    assert f["dividend_yield"] == 0.032


def test_get_company_info_parses_overview():
    src = AlphaVantageSource(api_key="demo")
    canned = {
        "Symbol": "IBM",
        "Name": "International Business Machines",
        "Sector": "TECHNOLOGY",
        "Industry": "COMPUTER & OFFICE EQUIPMENT",
        "Description": "IBM is an American multinational technology corporation.",
    }
    with patch.object(alphavantage_source.requests, "get", side_effect=_mock_get(canned)):
        info = src.get_company_info("IBM")
    assert info is not None
    assert info["name"] == "International Business Machines"
    assert info["sector"] == "TECHNOLOGY"
    assert info["industry"] == "COMPUTER & OFFICE EQUIPMENT"
    assert "IBM is an American" in info["description"]


def test_get_history_always_none():
    """yfinance owns history — this source explicitly returns None."""
    src = AlphaVantageSource(api_key="demo")
    assert src.get_history("IBM") is None
