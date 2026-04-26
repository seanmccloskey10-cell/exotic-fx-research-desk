"""Budget module tests — pure functions + tmp_path I/O, no network."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from lib.budget import (
    ESTIMATED_COST_PER_BRIEFING,
    MODEL_ID,
    UsageEntry,
    append_usage,
    compute_cost,
    compute_status,
    minutes_since_last,
    month_total,
    read_usage_log,
)


# ---------- Cost math ----------

def test_compute_cost_sonnet_46():
    # 1M input + 1M output = $3 + $15 = $18
    assert compute_cost(1_000_000, 1_000_000) == pytest.approx(18.0)
    # Zero
    assert compute_cost(0, 0) == 0.0
    # Realistic briefing: 5000 in, 1500 out
    cost = compute_cost(5000, 1500)
    assert cost == pytest.approx(5000 / 1e6 * 3 + 1500 / 1e6 * 15)
    assert cost < ESTIMATED_COST_PER_BRIEFING  # our $0.05 estimate is conservative


def test_compute_cost_unknown_model_raises():
    # Guarding against silent mis-pricing if someone swaps the model.
    with pytest.raises(ValueError):
        compute_cost(100, 100, model="claude-opus-4-7")


# ---------- Usage entry roundtrip ----------

def test_usage_entry_json_roundtrip():
    e = UsageEntry(
        timestamp=datetime(2026, 4, 21, 14, 30, 0),
        model=MODEL_ID,
        input_tokens=5000,
        output_tokens=1500,
        cost_usd=0.0375,
    )
    parsed = UsageEntry.from_dict(json.loads(e.to_json()))
    assert parsed is not None
    assert parsed.timestamp == e.timestamp
    assert parsed.input_tokens == 5000
    assert parsed.output_tokens == 1500
    assert parsed.cost_usd == pytest.approx(0.0375)


def test_usage_entry_from_dict_rejects_garbage():
    assert UsageEntry.from_dict({"nope": 1}) is None
    assert UsageEntry.from_dict({"timestamp": "not a date"}) is None


# ---------- Read / append ----------

def test_append_and_read_roundtrip(tmp_path):
    log = tmp_path / ".usage.jsonl"
    e1 = UsageEntry(datetime(2026, 4, 1, 10), MODEL_ID, 1000, 500, 0.0105)
    e2 = UsageEntry(datetime(2026, 4, 15, 11), MODEL_ID, 2000, 800, 0.018)
    append_usage(log, e1)
    append_usage(log, e2)
    entries = read_usage_log(log)
    assert len(entries) == 2
    assert entries[0].input_tokens == 1000
    assert entries[1].output_tokens == 800


def test_read_returns_empty_for_missing_file(tmp_path):
    assert read_usage_log(tmp_path / "does-not-exist.jsonl") == []


def test_read_skips_malformed_lines(tmp_path):
    log = tmp_path / ".usage.jsonl"
    log.write_text(
        '{"timestamp":"2026-04-01T10:00:00","model":"claude-sonnet-4-6","input_tokens":100,"output_tokens":50,"cost_usd":0.001}\n'
        "this is not json\n"
        '{"bad":"entry"}\n'
        '{"timestamp":"2026-04-02T10:00:00","model":"claude-sonnet-4-6","input_tokens":200,"output_tokens":100,"cost_usd":0.002}\n',
        encoding="utf-8",
    )
    entries = read_usage_log(log)
    assert len(entries) == 2
    assert entries[0].input_tokens == 100
    assert entries[1].input_tokens == 200


# ---------- Month total ----------

def test_month_total_filters_by_current_month():
    entries = [
        UsageEntry(datetime(2026, 3, 30, 12), MODEL_ID, 100, 50, 0.01),  # last month
        UsageEntry(datetime(2026, 4, 1, 12), MODEL_ID, 200, 100, 0.02),
        UsageEntry(datetime(2026, 4, 15, 12), MODEL_ID, 300, 150, 0.03),
        UsageEntry(datetime(2026, 5, 1, 12), MODEL_ID, 400, 200, 0.04),  # next month
    ]
    total = month_total(entries, now=datetime(2026, 4, 20, 10))
    assert total == pytest.approx(0.05)


def test_month_total_zero_for_empty():
    assert month_total([], now=datetime(2026, 4, 20)) == 0.0


# ---------- Rate limit ----------

def test_minutes_since_last_picks_newest():
    entries = [
        UsageEntry(datetime(2026, 4, 20, 10), MODEL_ID, 100, 50, 0.01),
        UsageEntry(datetime(2026, 4, 20, 12), MODEL_ID, 100, 50, 0.01),  # newest
        UsageEntry(datetime(2026, 4, 20, 11), MODEL_ID, 100, 50, 0.01),
    ]
    mins = minutes_since_last(entries, now=datetime(2026, 4, 20, 13))
    assert mins == pytest.approx(60.0)


def test_minutes_since_last_none_for_empty():
    assert minutes_since_last([], now=datetime(2026, 4, 20)) is None


def test_minutes_since_last_handles_tz_aware():
    """If an entry was written with a tz-aware timestamp, comparison still works."""
    tz_aware = UsageEntry(
        datetime(2026, 4, 20, 10, tzinfo=timezone.utc),
        MODEL_ID,
        100,
        50,
        0.01,
    )
    mins = minutes_since_last([tz_aware], now=datetime(2026, 4, 20, 11, 30))
    # UTC 10:00 -> local; diff should be non-negative.
    assert mins is not None
    assert mins >= 0


# ---------- Compute status ----------

def test_compute_status_is_capped_when_at_limit(tmp_path):
    log = tmp_path / ".usage.jsonl"
    append_usage(log, UsageEntry(datetime.now(), MODEL_ID, 1_000_000, 1_000_000, 5.00))
    status = compute_status(
        log_path=log, monthly_cap_usd=5.00, min_minutes_between=60
    )
    assert status.is_capped is True
    assert status.pct_used == 1.0


def test_compute_status_is_rate_limited_recent_entry(tmp_path):
    log = tmp_path / ".usage.jsonl"
    # Just generated — 0 minutes ago.
    append_usage(log, UsageEntry(datetime.now(), MODEL_ID, 100, 50, 0.01))
    status = compute_status(
        log_path=log, monthly_cap_usd=5.00, min_minutes_between=60
    )
    assert status.is_rate_limited is True
    assert status.minutes_until_allowed is not None
    assert status.minutes_until_allowed <= 60


def test_compute_status_not_rate_limited_after_window(tmp_path):
    log = tmp_path / ".usage.jsonl"
    old = datetime.now() - timedelta(minutes=90)
    append_usage(log, UsageEntry(old, MODEL_ID, 100, 50, 0.01))
    status = compute_status(
        log_path=log, monthly_cap_usd=5.00, min_minutes_between=60
    )
    assert status.is_rate_limited is False


def test_compute_status_empty_log(tmp_path):
    log = tmp_path / ".usage.jsonl"
    status = compute_status(
        log_path=log, monthly_cap_usd=5.00, min_minutes_between=60
    )
    assert status.month_spend == 0.0
    assert status.is_capped is False
    assert status.is_rate_limited is False
    assert status.minutes_since_last is None


def test_compute_status_next_month_start(tmp_path):
    log = tmp_path / ".usage.jsonl"
    status = compute_status(
        log_path=log,
        monthly_cap_usd=5.00,
        min_minutes_between=60,
        now=datetime(2026, 4, 21),
    )
    assert status.next_month_start == datetime(2026, 5, 1)


def test_compute_status_next_month_rolls_year(tmp_path):
    log = tmp_path / ".usage.jsonl"
    status = compute_status(
        log_path=log,
        monthly_cap_usd=5.00,
        min_minutes_between=60,
        now=datetime(2026, 12, 15),
    )
    assert status.next_month_start == datetime(2027, 1, 1)
