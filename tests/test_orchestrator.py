"""Orchestrator cascade tests — pure unit tests with fake sources."""

from __future__ import annotations

from typing import Optional

import pandas as pd

from data_sources.base import DataSource
from data_sources.orchestrator import DataOrchestrator


class FakeSource(DataSource):
    def __init__(
        self,
        name: str,
        configured: bool,
        quote_result: Optional[dict] = None,
        raise_on_quote: bool = False,
    ):
        self.name = name
        self._configured = configured
        self._quote_result = quote_result
        self._raise_on_quote = raise_on_quote

    def is_configured(self) -> bool:
        return self._configured

    def get_quote(self, ticker: str) -> Optional[dict]:
        if self._raise_on_quote:
            raise RuntimeError("boom")
        return self._quote_result

    def get_fundamentals(self, ticker: str):
        return None

    def get_history(self, ticker: str, period: str = "1y", interval: str = "1d"):
        return None

    def get_company_info(self, ticker: str):
        return None


def test_cascade_first_source_wins():
    s1 = FakeSource("a", True, quote_result={"price": 1.0, "source": "a"})
    s2 = FakeSource("b", True, quote_result={"price": 2.0, "source": "b"})
    orch = DataOrchestrator([s1, s2])
    result = orch.get_quote("X")
    assert result["source"] == "a"


def test_cascade_skips_unconfigured():
    s1 = FakeSource("a", configured=False, quote_result={"price": 1.0, "source": "a"})
    s2 = FakeSource("b", configured=True, quote_result={"price": 2.0, "source": "b"})
    orch = DataOrchestrator([s1, s2])
    assert orch.get_quote("X")["source"] == "b"


def test_cascade_falls_through_on_none():
    s1 = FakeSource("a", True, quote_result=None)
    s2 = FakeSource("b", True, quote_result={"price": 2.0, "source": "b"})
    orch = DataOrchestrator([s1, s2])
    assert orch.get_quote("X")["source"] == "b"


def test_cascade_catches_exceptions():
    s1 = FakeSource("a", True, raise_on_quote=True)
    s2 = FakeSource("b", True, quote_result={"price": 2.0, "source": "b"})
    orch = DataOrchestrator([s1, s2])
    assert orch.get_quote("X")["source"] == "b"


def test_cascade_all_fail_returns_none():
    s1 = FakeSource("a", True, quote_result=None)
    s2 = FakeSource("b", True, quote_result=None)
    orch = DataOrchestrator([s1, s2])
    assert orch.get_quote("X") is None


def test_status_reports_all_sources():
    s1 = FakeSource("a", True)
    s2 = FakeSource("b", False)
    orch = DataOrchestrator([s1, s2])
    status = orch.status()
    assert {"name": "a", "active": True} in status
    assert {"name": "b", "active": False} in status
