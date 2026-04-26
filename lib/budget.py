"""Anthropic budget tracking + rate limiting.

Single-purpose module — encapsulates every piece of accounting state so the
briefing view can stay focused on UX. Per PRD §5.6, ALL of the following
safeguards MUST hold; any change here needs to preserve them:

1. Budget cap read from ANTHROPIC_MONTHLY_BUDGET_USD (default $5/month).
2. Rate limit read from ANTHROPIC_MIN_MINUTES_BETWEEN_BRIEFINGS (default 60).
3. Usage ledger at briefings/.usage.jsonl (append-only; gitignored).
4. "Current month" is system local time — matches Roula's clock (Dubai).
5. Hard cap: when month spend >= cap, `is_capped()` returns True; the UI
   MUST disable the button. Only way to re-enable: edit .env manually.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

log = logging.getLogger(__name__)

# --- Pricing: Claude Sonnet 4.6 (USD per million tokens) ---
# Source: Anthropic API pricing page. Update here if pricing changes.
SONNET_46_INPUT_PER_M = 3.00
SONNET_46_OUTPUT_PER_M = 15.00

# Estimate displayed pre-flight on the Generate button. Based on a typical
# briefing: ~5K input tokens + ~1.5K output tokens -> ~$0.04. Rounded up.
ESTIMATED_COST_PER_BRIEFING = 0.05

# Model ID — locked per PRD §5.5.
MODEL_ID = "claude-sonnet-4-6"


def compute_cost(input_tokens: int, output_tokens: int, model: str = MODEL_ID) -> float:
    """Compute USD cost for an Anthropic call. Sonnet 4.6 pricing only."""
    # If someone swaps the model, fail loud rather than silently mis-price.
    if model != MODEL_ID:
        raise ValueError(
            f"compute_cost only knows {MODEL_ID} pricing; got {model}. "
            "Update lib/budget.py with the new model's rates."
        )
    return (input_tokens / 1_000_000.0) * SONNET_46_INPUT_PER_M + (
        output_tokens / 1_000_000.0
    ) * SONNET_46_OUTPUT_PER_M


@dataclass
class UsageEntry:
    timestamp: datetime
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float

    def to_json(self) -> str:
        return json.dumps(
            {
                "timestamp": self.timestamp.isoformat(),
                "model": self.model,
                "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens,
                "cost_usd": round(self.cost_usd, 6),
            }
        )

    @classmethod
    def from_dict(cls, d: dict) -> Optional["UsageEntry"]:
        try:
            ts = datetime.fromisoformat(d["timestamp"])
            return cls(
                timestamp=ts,
                model=d.get("model", MODEL_ID),
                input_tokens=int(d.get("input_tokens", 0)),
                output_tokens=int(d.get("output_tokens", 0)),
                cost_usd=float(d.get("cost_usd", 0.0)),
            )
        except (KeyError, ValueError, TypeError):
            return None


def read_usage_log(path: Path) -> List[UsageEntry]:
    """Read every entry in the JSONL log. Corrupt lines are skipped silently."""
    if not path.exists():
        return []
    entries: List[UsageEntry] = []
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    log.warning("Skipping malformed usage log line: %r", line[:80])
                    continue
                e = UsageEntry.from_dict(d)
                if e is not None:
                    entries.append(e)
    except OSError as e:
        log.warning("Could not read usage log %s: %s", path, e)
    return entries


def append_usage(path: Path, entry: UsageEntry) -> None:
    """Append one entry. Creates the file if missing."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(entry.to_json() + "\n")


def month_total(entries: List[UsageEntry], now: Optional[datetime] = None) -> float:
    """Sum of cost_usd for entries in the same (year, month) as `now`.

    Timezone policy: system local time (matches Roula's clock).
    """
    if now is None:
        now = datetime.now()
    total = 0.0
    for e in entries:
        if e.timestamp.year == now.year and e.timestamp.month == now.month:
            total += e.cost_usd
    return total


def minutes_since_last(
    entries: List[UsageEntry], now: Optional[datetime] = None
) -> Optional[float]:
    """Minutes since the newest entry, or None if log is empty."""
    if not entries:
        return None
    if now is None:
        now = datetime.now()
    # Entries may be tz-aware or naive. Coerce to naive local for the diff.
    latest = max(entries, key=lambda e: _strip_tz(e.timestamp))
    last = _strip_tz(latest.timestamp)
    delta = now - last
    return delta.total_seconds() / 60.0


def _strip_tz(dt: datetime) -> datetime:
    """Coerce tz-aware timestamps to naive local time for comparison."""
    if dt.tzinfo is None:
        return dt
    return dt.astimezone().replace(tzinfo=None)


@dataclass
class BudgetStatus:
    month_spend: float
    month_cap: float
    is_capped: bool
    minutes_since_last: Optional[float]
    min_minutes_between: int
    is_rate_limited: bool
    minutes_until_allowed: Optional[float]
    next_month_start: datetime

    @property
    def pct_used(self) -> float:
        if self.month_cap <= 0:
            return 0.0
        return min(1.0, self.month_spend / self.month_cap)


def compute_status(
    log_path: Path,
    monthly_cap_usd: float,
    min_minutes_between: int,
    now: Optional[datetime] = None,
) -> BudgetStatus:
    """One-shot snapshot of the budget state for the UI to render."""
    if now is None:
        now = datetime.now()
    entries = read_usage_log(log_path)
    spend = month_total(entries, now=now)
    mins_since = minutes_since_last(entries, now=now)

    is_capped = spend >= monthly_cap_usd
    is_rate_limited = mins_since is not None and mins_since < min_minutes_between
    mins_until = (
        None
        if mins_since is None
        else max(0.0, min_minutes_between - mins_since)
    )

    # First day of next month, at midnight local.
    if now.month == 12:
        next_month = datetime(now.year + 1, 1, 1)
    else:
        next_month = datetime(now.year, now.month + 1, 1)

    return BudgetStatus(
        month_spend=spend,
        month_cap=monthly_cap_usd,
        is_capped=is_capped,
        minutes_since_last=mins_since,
        min_minutes_between=min_minutes_between,
        is_rate_limited=is_rate_limited,
        minutes_until_allowed=mins_until,
        next_month_start=next_month,
    )
