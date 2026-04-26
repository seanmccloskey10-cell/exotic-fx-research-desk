"""Config loading — tickers, env vars, feature flags.

Timezone decision (per PRD blocker #4): system local time for all date
boundaries (same-day briefing cache, monthly budget rollover). the user is in
Dubai (UTC+4); system local matches what her clock shows.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TICKERS_PATH = PROJECT_ROOT / "config" / "tickers.yaml"
ENV_PATH = PROJECT_ROOT / ".env"

# Load .env once at import time. Silent if missing — the app still works
# because yfinance needs no key.
load_dotenv(ENV_PATH)


@dataclass(frozen=True)
class Ticker:
    symbol: str
    name: str = ""
    note: str = ""


@dataclass(frozen=True)
class Settings:
    tickers: List[Ticker]
    finnhub_key: str
    alphavantage_key: str
    anthropic_key: str
    anthropic_monthly_budget_usd: float
    anthropic_min_minutes_between_briefings: int

    # Derived flags — views check these rather than testing keys directly.
    @property
    def has_finnhub(self) -> bool:
        return bool(self.finnhub_key.strip())

    @property
    def has_alphavantage(self) -> bool:
        return bool(self.alphavantage_key.strip())

    @property
    def has_anthropic(self) -> bool:
        return bool(self.anthropic_key.strip())


def _load_tickers() -> List[Ticker]:
    if not TICKERS_PATH.exists():
        return []
    with TICKERS_PATH.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    entries = data.get("tickers", []) or []
    seen: set[str] = set()
    out: List[Ticker] = []
    for e in entries:
        if not (isinstance(e, dict) and e.get("symbol")):
            continue
        # Strip + upper so "  tsla " and "TSLA" resolve identically, and
        # dedupe so a duplicate entry in tickers.yaml doesn't render twice.
        symbol = str(e["symbol"]).strip().upper()
        if not symbol or symbol in seen:
            continue
        seen.add(symbol)
        out.append(
            Ticker(
                symbol=symbol,
                name=str(e.get("name", "")).strip(),
                note=str(e.get("note", "")).strip(),
            )
        )
    return out


def _get_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def load_settings() -> Settings:
    return Settings(
        tickers=_load_tickers(),
        finnhub_key=os.getenv("FINNHUB_API_KEY", "") or "",
        alphavantage_key=os.getenv("ALPHAVANTAGE_API_KEY", "") or "",
        anthropic_key=os.getenv("ANTHROPIC_API_KEY", "") or "",
        anthropic_monthly_budget_usd=_get_float("ANTHROPIC_MONTHLY_BUDGET_USD", 5.00),
        anthropic_min_minutes_between_briefings=_get_int(
            "ANTHROPIC_MIN_MINUTES_BETWEEN_BRIEFINGS", 60
        ),
    )


def env_path() -> Path:
    return ENV_PATH


def project_root() -> Path:
    return PROJECT_ROOT
