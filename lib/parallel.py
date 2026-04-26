"""Parallel fetch helper — runs N data-source calls concurrently.

Used by views to issue 5+ yfinance calls in parallel instead of serially.
On a warm yfinance cache this has no effect, but on a cold start it
collapses ~2.5s of sequential `Ticker.info` calls into ~600ms.

Error isolation: each worker returns (ticker, result) or (ticker, None) on
exception. One failing ticker never takes the whole batch down.

Usage:
    from lib.parallel import fetch_all

    results = fetch_all(
        ["CRDO", "HIMS", "BABA"],
        lambda sym: orch.get_quote(sym),
    )
    # results == {"CRDO": {...}, "HIMS": {...}, "BABA": None}
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Iterable, TypeVar

log = logging.getLogger(__name__)

T = TypeVar("T")

# yfinance's internal session is thread-safe; 8 concurrent workers is well
# below Yahoo Finance's soft rate limit and saturates a typical home network.
DEFAULT_MAX_WORKERS = 8


def fetch_all(
    tickers: Iterable[str],
    fetch: Callable[[str], T],
    max_workers: int = DEFAULT_MAX_WORKERS,
) -> Dict[str, T | None]:
    """Call `fetch(ticker)` for each ticker concurrently.

    Returns a dict keyed by ticker preserving input iteration order.
    Exceptions in a worker are caught and surfaced as None — caller's
    downstream code already handles None (orchestrator cascade + view
    rendering).
    """
    symbols = list(tickers)
    if not symbols:
        return {}

    results: Dict[str, T | None] = {s: None for s in symbols}
    # ThreadPoolExecutor max_workers defaults are fine but we cap for
    # predictability when watchlists grow.
    workers = min(max_workers, len(symbols))
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="erd-fetch") as ex:
        futures = {ex.submit(fetch, s): s for s in symbols}
        for fut in as_completed(futures):
            sym = futures[fut]
            try:
                results[sym] = fut.result()
            except Exception as e:
                log.warning("Parallel fetch failed for %s: %s", sym, e)
                results[sym] = None
    return results
