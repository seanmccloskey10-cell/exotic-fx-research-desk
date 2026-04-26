"""Parallel fetch helper tests — verify concurrency + error isolation."""

from __future__ import annotations

import threading
import time

from lib.parallel import fetch_all


def test_fetch_all_preserves_keys():
    result = fetch_all(["A", "B", "C"], lambda s: s.lower())
    assert result == {"A": "a", "B": "b", "C": "c"}


def test_fetch_all_empty_input():
    assert fetch_all([], lambda s: s) == {}


def test_fetch_all_single_ticker():
    assert fetch_all(["AAPL"], lambda s: {"price": 42}) == {"AAPL": {"price": 42}}


def test_fetch_all_isolates_exceptions():
    def flaky(sym: str) -> str:
        if sym == "BAD":
            raise RuntimeError("boom")
        return sym.lower()

    result = fetch_all(["A", "BAD", "C"], flaky)
    assert result["A"] == "a"
    assert result["BAD"] is None
    assert result["C"] == "c"


def test_fetch_all_actually_runs_concurrently():
    """Each call sleeps 200ms; 5 serial = 1.0s, parallel should be ~200ms."""
    seen_threads: set[int] = set()
    lock = threading.Lock()

    def slow(_sym: str) -> int:
        with lock:
            seen_threads.add(threading.get_ident())
        time.sleep(0.2)
        return 1

    start = time.time()
    fetch_all(["A", "B", "C", "D", "E"], slow)
    elapsed = time.time() - start

    assert elapsed < 0.8, f"parallel fetch took {elapsed:.2f}s — not concurrent"
    # At least 2 distinct threads must have run work.
    assert len(seen_threads) >= 2
