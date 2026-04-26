"""Market-hours classifier tests — pure-function, no network."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from lib.market_hours import current_status

ET = ZoneInfo("America/New_York")


def _et(year, month, day, hour, minute=0):
    return datetime(year, month, day, hour, minute, tzinfo=ET)


def test_regular_session_tuesday_noon():
    # Tuesday 2026-04-21 at 12:00 ET
    s = current_status(_et(2026, 4, 21, 12))
    assert s.state == "regular"
    assert s.label == "Open"
    assert "12:00 ET" in s.et_time


def test_pre_market_tuesday_0500():
    s = current_status(_et(2026, 4, 21, 5))
    assert s.state == "pre"
    assert s.label == "Pre-market"


def test_pre_market_cutoff_at_0930():
    # 09:30 is the boundary — starts counting as regular.
    s = current_status(_et(2026, 4, 21, 9, 30))
    assert s.state == "regular"


def test_after_hours_tuesday_1800():
    s = current_status(_et(2026, 4, 21, 18))
    assert s.state == "after"
    assert s.label == "After-hours"


def test_regular_close_at_1600_flips_to_after():
    s = current_status(_et(2026, 4, 21, 16))
    assert s.state == "after"


def test_after_hours_ends_at_2000():
    # 20:00 -> closed
    s = current_status(_et(2026, 4, 21, 20))
    assert s.state == "closed"


def test_late_night_closed():
    s = current_status(_et(2026, 4, 21, 23))
    assert s.state == "closed"


def test_weekend_saturday():
    s = current_status(_et(2026, 4, 25, 12))  # Saturday
    assert s.state == "closed"
    assert s.label == "Closed"


def test_weekend_sunday():
    s = current_status(_et(2026, 4, 26, 12))  # Sunday
    assert s.state == "closed"


def test_handles_naive_datetime():
    """Naive datetimes are treated as already in ET rather than crashing."""
    s = current_status(datetime(2026, 4, 21, 12))
    # Would be 12:00 local time; whether it's open depends on the runner's tz,
    # but the call must return SOMETHING, not raise.
    assert s.state in {"regular", "pre", "after", "closed"}
