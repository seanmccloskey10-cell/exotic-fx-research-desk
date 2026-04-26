"""Briefing engine tests — mocks the Anthropic client, no network."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from lib.briefing_engine import (
    BriefingAPIError,
    BriefingError,
    BriefingNoKey,
    BriefingRateLimited,
    BriefingResult,
    build_watchlist_context,
    generate_briefing,
    load_prompt_template,
    render_user_prompt,
    strip_frontmatter,
)


# ---------- Fixtures ----------

class _Ticker:
    def __init__(self, symbol, name="", note=""):
        self.symbol = symbol
        self.name = name
        self.note = note


class _Settings:
    def __init__(self, tickers):
        self.tickers = tickers


def _synthetic_history(n: int = 260) -> pd.DataFrame:
    """OHLCV DataFrame long enough (>= 200 bars) for every technical indicator."""
    idx = pd.date_range("2025-04-20", periods=n, freq="B")
    rng = np.random.default_rng(42)
    # Trending series with moderate noise — gives all indicators real values.
    trend = np.linspace(80.0, 120.0, n)
    noise = rng.normal(0, 1.2, n).cumsum() * 0.3
    close = trend + noise
    return pd.DataFrame(
        {
            "Open": close - 0.3,
            "High": close + 0.6,
            "Low": close - 0.6,
            "Close": close,
            "Volume": rng.integers(1_000_000, 3_000_000, n),
        },
        index=idx,
    )


class _FakeOrch:
    """Stands in for DataOrchestrator. Every method returns canned data."""

    def __init__(self, **overrides):
        self._data = {
            "quote": {"price": 100.0, "change_pct": 1.5},
            "fund": {"market_cap": 1e9, "pe_ratio": 20.0, "pb_ratio": 3.0, "dividend_yield": 0.02, "roe": 0.15, "fifty_two_week_high": 120.0, "fifty_two_week_low": 80.0},
            "info": {"name": "Test Inc", "sector": "Tech", "industry": "Software"},
            "news": [
                {
                    "title": "Headline A",
                    "publisher": "Reuters",
                    "published_at": datetime(2026, 4, 20),
                    "url": "https://example.com/a",
                    "summary": "A short recap of the news.",
                },
                {
                    "title": "Headline B",
                    "publisher": "Bloomberg",
                    "published_at": datetime(2026, 4, 19),
                    "url": "https://example.com/b",
                    "summary": "Another recap.",
                },
            ],
            "earnings": {
                "next_date": date(2026, 5, 1),
                "eps_estimate": 1.25,
                "time": "amc",
            },
            # Default: a 260-bar synthetic series so all technicals compute.
            "history": _synthetic_history(),
        }
        self._data.update(overrides)

    def get_quote(self, t):
        return self._data["quote"]

    def get_fundamentals(self, t):
        return self._data["fund"]

    def get_company_info(self, t):
        return self._data["info"]

    def get_news(self, t):
        return self._data["news"]

    def get_earnings(self, t):
        return self._data["earnings"]

    def get_history(self, t, period=None, interval=None):
        return self._data["history"]


# ---------- Context builder ----------

def test_build_context_includes_every_ticker():
    settings = _Settings([_Ticker("CRDO", "Credo"), _Ticker("HIMS", "Hims & Hers")])
    ctx = build_watchlist_context(settings, _FakeOrch())
    assert len(ctx["tickers"]) == 2
    assert ctx["tickers"][0]["ticker"] == "CRDO"
    assert ctx["tickers"][1]["ticker"] == "HIMS"
    # v2 prompt: local ISO + ET + session, no bare `generated_at`.
    assert ctx["generated_at_local"]
    assert "ET" in ctx["generated_at_et"]
    assert ctx["market_session"] in {"Open", "Pre-market", "After-hours", "Closed"}


def test_build_context_caps_news_at_three_per_ticker():
    long_news = [
        {"title": f"H{i}", "publisher": "X", "published_at": datetime(2026, 4, 20)}
        for i in range(10)
    ]
    settings = _Settings([_Ticker("CRDO")])
    orch = _FakeOrch(news=long_news)
    ctx = build_watchlist_context(settings, orch)
    assert len(ctx["tickers"][0]["recent_news"]) == 3


def test_build_context_handles_missing_data_gracefully():
    settings = _Settings([_Ticker("CRDO")])
    orch = _FakeOrch(
        quote=None, fund=None, info=None, news=[], earnings=None, history=None
    )
    ctx = build_watchlist_context(settings, orch)
    entry = ctx["tickers"][0]
    assert entry["ticker"] == "CRDO"
    assert entry["price"] is None
    assert entry["recent_news"] == []
    assert entry["upcoming_earnings"] is None
    # v3: technicals must always be present; values degrade to None when
    # history is unavailable rather than raising.
    t = entry["technicals"]
    assert t["rsi_14"] is None
    assert t["rsi_state"] == "Insufficient data"
    assert t["macd_line"] is None
    assert t["sma_200"] is None


def test_build_context_v3_technicals_present():
    """Every ticker entry gets a complete `technicals` subdict."""
    settings = _Settings([_Ticker("CRDO", "Credo")])
    ctx = build_watchlist_context(settings, _FakeOrch())
    t = ctx["tickers"][0]["technicals"]
    expected_keys = {
        "rsi_14",
        "rsi_state",
        "macd_line",
        "macd_signal",
        "macd_histogram",
        "macd_crossover",
        "macd_days_since_crossover",
        "sma_20",
        "sma_50",
        "sma_200",
        "price_vs_sma_200_pct",
    }
    assert set(t.keys()) == expected_keys


def test_build_context_v3_rsi_in_valid_range():
    """RSI(14) from a real-looking series must land in [0, 100]."""
    settings = _Settings([_Ticker("CRDO")])
    ctx = build_watchlist_context(settings, _FakeOrch())
    rsi_val = ctx["tickers"][0]["technicals"]["rsi_14"]
    assert rsi_val is not None
    assert 0.0 <= rsi_val <= 100.0


def test_build_context_v3_macd_state_label_valid():
    """Crossover label must be one of the three documented strings."""
    settings = _Settings([_Ticker("CRDO")])
    ctx = build_watchlist_context(settings, _FakeOrch())
    cross = ctx["tickers"][0]["technicals"]["macd_crossover"]
    assert cross in {"bullish", "bearish", "none"}


def test_prompt_version_is_current():
    """Sanity: the module-level constant is the current prompt stamp.

    Bump the expected prefix when the prompt payload shape changes materially
    so old cached briefings remain distinguishable from new ones on disk.
    """
    from lib.briefing_engine import PROMPT_VERSION
    assert PROMPT_VERSION.startswith("v4-")


def test_build_context_v4_extended_fundamentals_present():
    """v4: payload surfaces forward_pe, eps, beta, profit_margin, debt_to_equity."""
    # Augment the canned fundamentals dict so the new keys are populated.
    fund = {
        "market_cap": 1e9,
        "pe_ratio": 20.0,
        "forward_pe": 18.0,
        "pb_ratio": 3.0,
        "eps": 2.5,
        "beta": 1.1,
        "profit_margin": 0.18,
        "debt_to_equity": 0.45,
        "dividend_yield": 0.02,
        "roe": 0.15,
        "fifty_two_week_high": 120.0,
        "fifty_two_week_low": 80.0,
    }
    settings = _Settings([_Ticker("CRDO")])
    ctx = build_watchlist_context(settings, _FakeOrch(fund=fund))
    entry = ctx["tickers"][0]
    for key in (
        "forward_pe",
        "eps",
        "beta",
        "profit_margin",
        "debt_to_equity",
    ):
        assert key in entry, f"v4 payload missing {key}"
        assert entry[key] == fund[key]


# ---------- Prompt parsing ----------

def test_load_prompt_template_reads_both_sections(tmp_path):
    p = tmp_path / "prompt.md"
    p.write_text(
        "# Header\n\n"
        "## System Prompt\n\n"
        "You are an assistant.\n\n"
        "## User Prompt\n\n"
        "Here is data: {{watchlist_json}}\n",
        encoding="utf-8",
    )
    system, user = load_prompt_template(p)
    assert "You are an assistant" in system
    assert "{{watchlist_json}}" in user


def test_load_prompt_template_raises_on_missing_sections(tmp_path):
    p = tmp_path / "prompt.md"
    p.write_text("No sections here.", encoding="utf-8")
    with pytest.raises(BriefingError):
        load_prompt_template(p)


def test_render_user_prompt_substitutes_variables():
    template = (
        "Data: {{watchlist_json}}\n"
        "Local: {{generated_at_local}}\n"
        "ET: {{generated_at_et}}\n"
        "Session: {{market_session}}"
    )
    ctx = {
        "tickers": [{"ticker": "X"}],
        "generated_at_local": "2026-04-21T14:00:00+01:00",
        "generated_at_et": "09:00 ET",
        "market_session": "Pre-market",
    }
    rendered = render_user_prompt(template, ctx)
    assert "ticker" in rendered
    assert "2026-04-21T14:00:00+01:00" in rendered
    assert "09:00 ET" in rendered
    assert "Pre-market" in rendered
    assert "{{" not in rendered  # no unsubstituted placeholders


def test_render_user_prompt_legacy_generated_at_placeholder():
    """Older prompt-template copies using `{{generated_at}}` must still work."""
    template = "At: {{generated_at}}"
    ctx = {
        "tickers": [],
        "generated_at_local": "2026-04-21T14:00:00+01:00",
        "generated_at_et": "09:00 ET",
        "market_session": "Pre-market",
    }
    rendered = render_user_prompt(template, ctx)
    # Legacy placeholder maps to local ISO
    assert "2026-04-21T14:00:00+01:00" in rendered


def test_headline_summary_includes_url():
    """News URLs must round-trip through context so Claude can cite + link."""
    from lib.briefing_engine import _headline_summary
    article = {
        "title": "Big news",
        "publisher": "Reuters",
        "published_at": datetime(2026, 4, 20),
        "url": "https://example.com/story",
        "summary": "Body of the article.",
    }
    out = _headline_summary(article)
    assert out["url"] == "https://example.com/story"
    assert out["summary"] == "Body of the article."
    assert out["publisher"] == "Reuters"


def test_headline_summary_truncates_long_summary():
    """Avoid blowing out input-token budget on noisy news items."""
    from lib.briefing_engine import _headline_summary
    long_summary = "word " * 200  # ~1000 chars
    article = {
        "title": "Story",
        "publisher": "X",
        "published_at": datetime(2026, 4, 20),
        "url": "https://x.com",
        "summary": long_summary,
    }
    out = _headline_summary(article)
    assert len(out["summary"]) <= 300
    assert out["summary"].endswith("...")


# ---------- Anthropic call (mocked) ----------

def _mock_response(text="# Sample briefing", in_tokens=5000, out_tokens=1200):
    resp = MagicMock()
    block = MagicMock()
    block.text = text
    resp.content = [block]
    resp.usage.input_tokens = in_tokens
    resp.usage.output_tokens = out_tokens
    return resp


def test_generate_briefing_no_key_raises():
    with pytest.raises(BriefingNoKey):
        generate_briefing("", "sys", "user")


def test_generate_briefing_success():
    with patch("anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.return_value = _mock_response()
        result = generate_briefing("sk-test", "sys prompt", "user prompt")
    assert result.markdown == "# Sample briefing"
    assert result.input_tokens == 5000
    assert result.output_tokens == 1200
    assert result.cost_usd > 0
    assert result.model == "claude-sonnet-4-6"


def test_generate_briefing_rate_limit_surfaces():
    import anthropic
    with patch("anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.side_effect = (
            anthropic.RateLimitError(
                "rate limited",
                response=MagicMock(status_code=429),
                body=None,
            )
        )
        with pytest.raises(BriefingRateLimited):
            generate_briefing("sk-test", "sys", "user")


def test_generate_briefing_connection_error_surfaces():
    import anthropic
    with patch("anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.side_effect = (
            anthropic.APIConnectionError(request=MagicMock())
        )
        with pytest.raises(BriefingAPIError):
            generate_briefing("sk-test", "sys", "user")


def test_generate_briefing_empty_response_raises():
    with patch("anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.return_value = _mock_response(text="")
        with pytest.raises(BriefingAPIError):
            generate_briefing("sk-test", "sys", "user")


def test_generate_briefing_cost_matches_usage():
    """The cost attached to the result must be computed from the response's usage."""
    with patch("anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.return_value = _mock_response(
            in_tokens=10_000, out_tokens=2_000
        )
        result = generate_briefing("sk-test", "sys", "user")
    # 10K/1M * $3 + 2K/1M * $15 = $0.03 + $0.03 = $0.06
    assert result.cost_usd == pytest.approx(0.06)


# ---------- Frontmatter ----------

def test_with_frontmatter_includes_provenance():
    from lib.briefing_engine import PROMPT_VERSION

    result = BriefingResult(
        markdown="# Weekly briefing\n\nBody text.",
        input_tokens=5000,
        output_tokens=1500,
        cost_usd=0.0375,
        model="claude-sonnet-4-6",
    )
    out = result.with_frontmatter(["CRDO", "HIMS"])
    # Frontmatter must appear at the top, bracketed by ---
    assert out.startswith("---\n")
    assert "model: claude-sonnet-4-6" in out
    assert f"prompt_version: {PROMPT_VERSION}" in out
    assert "input_tokens: 5000" in out
    assert "output_tokens: 1500" in out
    assert "cost_usd: 0.037500" in out
    assert "watchlist: [CRDO, HIMS]" in out
    # Body preserved
    assert "# Weekly briefing" in out
    assert "Body text." in out


def test_strip_frontmatter_round_trip():
    result = BriefingResult(
        markdown="# Title\n\nBody.",
        input_tokens=100,
        output_tokens=50,
        cost_usd=0.001,
        model="claude-sonnet-4-6",
    )
    with_fm = result.with_frontmatter(["X"])
    stripped = strip_frontmatter(with_fm)
    assert stripped == "# Title\n\nBody."


def test_strip_frontmatter_passthrough_when_absent():
    plain = "# No frontmatter here\n\nJust body."
    assert strip_frontmatter(plain) == plain


def test_strip_frontmatter_handles_malformed():
    """If frontmatter opens but never closes, return the input unchanged."""
    malformed = "---\nnever closes\nno end marker\n"
    assert strip_frontmatter(malformed) == malformed
