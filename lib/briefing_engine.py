"""AI briefing engine — context builder + Anthropic caller.

Per PRD §5.6 #6, the Anthropic SDK is imported nowhere else in the codebase.
Every Anthropic call goes through `generate_briefing` below, which is ONLY
invoked from `views/briefing.py` inside a dialog's Confirm button block.

Split of concerns:
- `build_watchlist_context` — gathers the watchlist state (pure function, no
  network after the orchestrator's caches have warmed).
- `load_prompt_template` — reads `config/briefing_prompt.md` and returns
  (system_prompt, user_prompt_template).
- `generate_briefing` — the single Anthropic call. Returns a (markdown,
  usage) tuple on success, or raises a subclass of `BriefingError` on
  every failure mode. The caller decides how to surface the failure — this
  module does not retry and does not fall back silently.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Tuple

from lib.budget import MODEL_ID, compute_cost
from lib.market_hours import current_status as current_market_status
from lib.parallel import fetch_all
from lib.technicals import (
    macd,
    macd_state,
    price_vs_ma,
    rsi,
    rsi_state,
    sma,
)

# Bump when the prompt template's structure changes in a way that affects
# output shape (new section, new instruction class, etc.). Recorded in the
# briefing frontmatter so two briefings from different prompt versions are
# comparable.
PROMPT_VERSION = "v4-2026-04-21"

log = logging.getLogger(__name__)

MAX_TOKENS = 2048  # cap the output; a briefing shouldn't need more
NEWS_PER_TICKER = 3  # headlines per ticker in the context payload
# Anthropic SDK's default timeout is 10 minutes — too long for an interactive
# UI where Roula is watching a spinner. 90s covers legitimate Sonnet latency
# with comfortable margin, and fails fast on network hangs.
ANTHROPIC_TIMEOUT_SECONDS = 90.0


# ---------- Exceptions ----------

class BriefingError(Exception):
    """Base for anything the briefing engine surfaces to the UI."""


class BriefingRateLimited(BriefingError):
    """Anthropic returned HTTP 429."""


class BriefingAPIError(BriefingError):
    """Generic Anthropic / network failure."""


class BriefingNoKey(BriefingError):
    """Tried to generate with no ANTHROPIC_API_KEY configured."""


# ---------- Context ----------

def _headline_summary(article: dict) -> dict:
    """Trim an article dict down to briefing-relevant fields.

    URL is included so Claude can cite links in the briefing and Roula can
    click through. Long summaries are truncated so a noisy news item doesn't
    blow out the input-token budget.
    """
    pub = article.get("published_at")
    summary = article.get("summary") or ""
    if summary and len(summary) > 300:
        summary = summary[:297].rstrip() + "..."
    return {
        "title": article.get("title"),
        "publisher": article.get("publisher"),
        "date": pub.strftime("%Y-%m-%d") if hasattr(pub, "strftime") else None,
        "url": article.get("url"),
        "summary": summary or None,
    }


_EMPTY_TECHNICALS = {
    "rsi_14": None,
    "rsi_state": "Insufficient data",
    "macd_line": None,
    "macd_signal": None,
    "macd_histogram": None,
    "macd_crossover": "none",
    "macd_days_since_crossover": None,
    "sma_20": None,
    "sma_50": None,
    "sma_200": None,
    "price_vs_sma_200_pct": None,
}


def _build_technicals(history, current_price) -> dict:
    """Per-ticker technical-indicator snapshot for the briefing payload.

    All values are floats or None; strings for categorical states. Units
    documented in config/briefing_prompt.md so Claude reads them the same
    way every time. `price_vs_sma_200_pct` is expressed as a percent (2.5
    = 2.5% above the 200-day SMA) to match `change_pct` in the payload.
    """
    if history is None or history.empty or "Close" not in history.columns:
        return dict(_EMPTY_TECHNICALS)
    close = history["Close"]
    rsi_val = rsi(close, period=14)
    macd_vals = macd(close) or {}
    macd_cross = macd_state(close)
    ma200 = sma(close, 200)
    price = current_price if current_price is not None else (
        float(close.iloc[-1]) if not close.empty else None
    )
    pct_vs_200_dec = price_vs_ma(price, ma200)
    return {
        "rsi_14": rsi_val,
        "rsi_state": rsi_state(rsi_val),
        "macd_line": macd_vals.get("macd"),
        "macd_signal": macd_vals.get("signal"),
        "macd_histogram": macd_vals.get("histogram"),
        "macd_crossover": macd_cross.get("crossover"),
        "macd_days_since_crossover": macd_cross.get("days_since_crossover"),
        "sma_20": sma(close, 20),
        "sma_50": sma(close, 50),
        "sma_200": ma200,
        "price_vs_sma_200_pct": (
            pct_vs_200_dec * 100.0 if pct_vs_200_dec is not None else None
        ),
    }


def build_watchlist_context(settings, orch) -> dict:
    """Assemble a compact JSON-safe dict describing the watchlist state.

    Shape is intentionally small so the prompt stays well under the input
    budget even as the watchlist grows. News is capped at NEWS_PER_TICKER
    items per ticker. Per-ticker technicals (RSI, MACD, SMAs) are computed
    from 1-year daily history so the briefing can reason across both
    fundamentals and technical state.
    """
    symbols = [t.symbol for t in settings.tickers]
    # Parallel-fetch history once up-front — needed for technicals and cheap
    # via the 15-min cache wrapper, but serial per-ticker was too slow when
    # the cache is cold.
    history_map = fetch_all(
        symbols, lambda s: orch.get_history(s, period="1y", interval="1d")
    )
    tickers_payload = []
    for t in settings.tickers:
        q = orch.get_quote(t.symbol) or {}
        f = orch.get_fundamentals(t.symbol) or {}
        info = orch.get_company_info(t.symbol) or {}
        news = orch.get_news(t.symbol) or []
        earnings = orch.get_earnings(t.symbol)
        technicals = _build_technicals(history_map.get(t.symbol), q.get("price"))

        tickers_payload.append(
            {
                "ticker": t.symbol,
                "name": info.get("name") or t.name,
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "price": q.get("price"),
                "change_pct": q.get("change_pct"),
                "market_cap": f.get("market_cap"),
                "pe_ratio": f.get("pe_ratio"),
                "forward_pe": f.get("forward_pe"),
                "pb_ratio": f.get("pb_ratio"),
                "eps": f.get("eps"),
                "beta": f.get("beta"),
                "profit_margin": f.get("profit_margin"),
                "debt_to_equity": f.get("debt_to_equity"),
                "dividend_yield": f.get("dividend_yield"),
                "roe": f.get("roe"),
                "fifty_two_week_high": f.get("fifty_two_week_high"),
                "fifty_two_week_low": f.get("fifty_two_week_low"),
                "technicals": technicals,
                "recent_news": [_headline_summary(a) for a in news[:NEWS_PER_TICKER]],
                "upcoming_earnings": (
                    {
                        "next_date": (
                            earnings["next_date"].isoformat()
                            if earnings and earnings.get("next_date")
                            else None
                        ),
                        "eps_estimate": earnings.get("eps_estimate") if earnings else None,
                        "time": earnings.get("time") if earnings else None,
                    }
                    if earnings
                    else None
                ),
            }
        )
    # Timestamps: Claude was inventing timezones when we passed naive ISO. Now
    # we pass system-local WITH offset + an explicit ET rendering (since US
    # market time is the canonical frame for equity briefings) + the live
    # market session state. Claude is instructed in the prompt to use THESE
    # values, never to guess.
    now_local = datetime.now().astimezone()
    market = current_market_status(now_local)
    return {
        "generated_at_local": now_local.isoformat(timespec="seconds"),
        "generated_at_et": market.et_time,
        "market_session": market.label,
        "tickers": tickers_payload,
    }


# ---------- Prompt template ----------

def load_prompt_template(path: Path) -> Tuple[str, str]:
    """Parse briefing_prompt.md into (system_prompt, user_prompt_template).

    The template file has two `## System Prompt` and `## User Prompt`
    sections; everything else in the file is explanatory text and ignored.
    """
    text = path.read_text(encoding="utf-8")

    sys_match = re.search(
        r"##\s*System Prompt\s*\n(.*?)(?=\n##\s|\Z)", text, re.DOTALL
    )
    usr_match = re.search(
        r"##\s*User Prompt\s*\n(.*?)(?=\n##\s|\Z)", text, re.DOTALL
    )
    if not sys_match or not usr_match:
        raise BriefingError(
            f"Could not parse {path.name}: expected '## System Prompt' and "
            "'## User Prompt' sections."
        )
    return sys_match.group(1).strip(), usr_match.group(1).strip()


def render_user_prompt(template: str, context: dict) -> str:
    """Substitute variables into the user prompt.

    Supported placeholders (all wrapped in double braces):
        {{watchlist_json}}    — list of ticker dicts, pretty-printed
        {{generated_at_local}} — ISO 8601 with tz offset
        {{generated_at_et}}   — "HH:MM ET"
        {{market_session}}    — "Open" / "Pre-market" / "After-hours" / "Closed"

    Legacy `{{generated_at}}` also substituted (maps to local) for backwards
    compatibility with older prompt-template copies.
    """
    watchlist_json = json.dumps(context["tickers"], indent=2, default=str)
    rendered = template.replace("{{watchlist_json}}", watchlist_json)
    rendered = rendered.replace(
        "{{generated_at_local}}", context.get("generated_at_local", "")
    )
    rendered = rendered.replace(
        "{{generated_at_et}}", context.get("generated_at_et", "")
    )
    rendered = rendered.replace(
        "{{market_session}}", context.get("market_session", "")
    )
    # Legacy placeholder — kept so an old prompt template doesn't break.
    rendered = rendered.replace(
        "{{generated_at}}", context.get("generated_at_local", "")
    )
    return rendered


# ---------- Anthropic call ----------

@dataclass
class BriefingResult:
    markdown: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    model: str

    def with_frontmatter(self, watchlist_symbols: list[str]) -> str:
        """Markdown prefixed with YAML provenance frontmatter.

        Used when persisting to `briefings/YYYY-MM-DD.md` so each cached
        briefing is self-documenting (when was it generated, which model,
        what did it cost, which prompt version).
        """
        fm = [
            "---",
            f"generated_at: {datetime.now().astimezone().isoformat(timespec='seconds')}",
            f"model: {self.model}",
            f"prompt_version: {PROMPT_VERSION}",
            f"input_tokens: {self.input_tokens}",
            f"output_tokens: {self.output_tokens}",
            f"cost_usd: {self.cost_usd:.6f}",
            f"watchlist: [{', '.join(watchlist_symbols)}]",
            "---",
            "",
        ]
        return "\n".join(fm) + self.markdown


def strip_frontmatter(markdown: str) -> str:
    """Remove a leading YAML frontmatter block if present, else return as-is.

    Used when rendering a cached briefing in the UI — we want the body only,
    not the raw YAML preamble.
    """
    if not markdown.startswith("---\n"):
        return markdown
    # Find the closing ---
    rest = markdown[4:]
    end = rest.find("\n---\n")
    if end < 0:
        return markdown
    return rest[end + 5:].lstrip("\n")


def generate_briefing(
    api_key: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = MAX_TOKENS,
) -> BriefingResult:
    """One Anthropic call. Returns `BriefingResult` on success; raises on failure.

    CRITICAL (PRD §5.6 #6): this is the only Anthropic call site in the app.
    It is imported and invoked only from `views/briefing.py` inside a dialog
    Confirm branch. Do not call from anywhere else, and do not add retry
    logic — PRD §5.6 #8 says no retries on 429.
    """
    if not api_key or not api_key.strip():
        raise BriefingNoKey("ANTHROPIC_API_KEY is not set")

    # Lazy import so the anthropic package is only touched when the user
    # actually triggers a briefing, not at app import time.
    try:
        import anthropic  # noqa: WPS433
    except ImportError as e:
        raise BriefingAPIError(f"anthropic package not installed: {e}")

    client = anthropic.Anthropic(
        api_key=api_key,
        timeout=ANTHROPIC_TIMEOUT_SECONDS,
    )

    try:
        response = client.messages.create(
            model=MODEL_ID,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
    except anthropic.RateLimitError as e:
        raise BriefingRateLimited(str(e))
    except anthropic.APIConnectionError as e:
        raise BriefingAPIError(f"Could not reach Anthropic: {e}")
    except anthropic.APITimeoutError as e:
        raise BriefingAPIError(
            f"Anthropic call timed out after {ANTHROPIC_TIMEOUT_SECONDS:.0f}s. "
            f"Try again; the app will not retry automatically."
        )
    except anthropic.APIStatusError as e:
        raise BriefingAPIError(f"Anthropic returned HTTP {e.status_code}: {e}")
    except anthropic.AnthropicError as e:
        raise BriefingAPIError(f"Anthropic SDK error: {e}")

    # Extract the markdown from the response.
    parts = []
    for block in response.content:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    markdown = "\n".join(parts).strip()
    if not markdown:
        raise BriefingAPIError("Anthropic returned an empty response.")

    input_tokens = int(getattr(response.usage, "input_tokens", 0) or 0)
    output_tokens = int(getattr(response.usage, "output_tokens", 0) or 0)
    cost_usd = compute_cost(input_tokens, output_tokens, MODEL_ID)

    return BriefingResult(
        markdown=markdown,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost_usd,
        model=MODEL_ID,
    )
