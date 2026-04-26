"""Provenance helper tests — just the pure catalogue + active-names logic.

`render_footer` itself is a Streamlit render, exercised indirectly by
`test_app_boots.py`.
"""

from __future__ import annotations

from lib.provenance import SOURCE_DESCRIPTIONS, _active_names


class _FakeOrch:
    def __init__(self, status):
        self._status = status

    def status(self):
        return self._status


def test_active_names_filters_inactive():
    orch = _FakeOrch(
        [
            {"name": "yfinance", "active": True},
            {"name": "finnhub", "active": True},
            {"name": "alphavantage", "active": False},
        ]
    )
    assert _active_names(orch) == ["yfinance", "finnhub"]


def test_active_names_empty_when_all_off():
    orch = _FakeOrch(
        [
            {"name": "yfinance", "active": False},
            {"name": "finnhub", "active": False},
        ]
    )
    assert _active_names(orch) == []


def test_source_descriptions_cover_all_known_sources():
    """Every source registered in orchestrator.build_default_orchestrator
    should have a descriptive entry — otherwise the sidebar falls back to
    a bare name and the user sees an unhelpful green dot.
    """
    expected = {"yfinance", "finnhub", "alphavantage"}
    assert expected.issubset(SOURCE_DESCRIPTIONS.keys())


def test_source_descriptions_have_required_fields():
    for name, meta in SOURCE_DESCRIPTIONS.items():
        for key in ("label", "role", "cost", "covers"):
            assert meta.get(key), f"{name}: missing {key}"
