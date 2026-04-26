"""US stock market session detection — for the sidebar indicator.

Checks the current time in US/Eastern against NYSE hours:
- Weekday 09:30 - 16:00 ET → regular session
- Weekday 04:00 - 09:30 ET → pre-market
- Weekday 16:00 - 20:00 ET → after-hours
- Otherwise → closed

Intentionally ignores market holidays (Thanksgiving, etc.) — this is a
sidebar hint, not a trading system. Listing them would mean an annual
maintenance burden and add a dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from typing import Optional

try:
    from zoneinfo import ZoneInfo  # stdlib, 3.9+
except ImportError:  # pragma: no cover
    ZoneInfo = None  # type: ignore

ET = ZoneInfo("America/New_York") if ZoneInfo else None

REGULAR_OPEN = time(9, 30)
REGULAR_CLOSE = time(16, 0)
PREMARKET_OPEN = time(4, 0)
AFTERHOURS_CLOSE = time(20, 0)


@dataclass(frozen=True)
class MarketStatus:
    state: str          # "regular" / "pre" / "after" / "closed"
    label: str          # human-readable: "Open", "Pre-market", etc.
    icon: str           # single emoji for sidebar rendering
    et_time: str        # "14:32 ET"


def current_status(now: Optional[datetime] = None) -> MarketStatus:
    """Return the NYSE session classification at `now` (default: wall-clock).

    `now` may be naive (assumed local) or timezone-aware. Converted to ET
    internally.
    """
    if now is None:
        now = datetime.now()
    if ET is None:
        return MarketStatus(
            state="unknown",
            label="Status unknown",
            icon="⚪",
            et_time="—",
        )

    now_et = now.astimezone(ET) if now.tzinfo else now.replace(tzinfo=ET)
    weekday = now_et.weekday()  # 0=Mon .. 6=Sun
    t = now_et.time()
    et_time_str = now_et.strftime("%H:%M ET")

    # Weekend — always closed.
    if weekday >= 5:
        return MarketStatus("closed", "Closed", "🔴", et_time_str)

    if REGULAR_OPEN <= t < REGULAR_CLOSE:
        return MarketStatus("regular", "Open", "🟢", et_time_str)
    if PREMARKET_OPEN <= t < REGULAR_OPEN:
        return MarketStatus("pre", "Pre-market", "🟡", et_time_str)
    if REGULAR_CLOSE <= t < AFTERHOURS_CLOSE:
        return MarketStatus("after", "After-hours", "🟡", et_time_str)
    return MarketStatus("closed", "Closed", "🔴", et_time_str)
