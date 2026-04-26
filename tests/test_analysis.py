"""Analysis view — tests for the peer-median helpers.

The previous watchlist-wide radar view was scrapped; per-stock fundamentals
now use median-across-the-rest-of-the-watchlist as peer context. These tests
cover the `_median` helper directly; `_collect_medians` is integration-ish
(talks to the orchestrator) and is exercised by the app-boots smoke test.
"""

from __future__ import annotations

from views.analysis import _median


def test_median_of_simple_list():
    assert _median([10.0, 20.0, 30.0]) == 20.0


def test_median_ignores_nones():
    # Three present values → median of those three, not counting the None.
    assert _median([10.0, None, 30.0, None, 20.0]) == 20.0


def test_median_all_none_returns_none():
    assert _median([None, None, None]) is None


def test_median_empty_returns_none():
    assert _median([]) is None


def test_median_even_count_averages_middle():
    # Standard statistics.median convention: average of the two middle values.
    assert _median([1.0, 2.0, 3.0, 4.0]) == 2.5


def test_median_single_value():
    assert _median([42.0]) == 42.0
