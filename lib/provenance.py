"""Data-provenance helpers — one place to answer "where did this data come from?".

Two surfaces:

- `render_footer(orch)` — a small caption at the bottom of each view listing
  the active data sources and their roles. Keeps attribution visible wherever
  Roula is looking.
- `SOURCE_DESCRIPTIONS` — richer descriptions used by the sidebar to unpack
  each source beyond a green dot.
"""

from __future__ import annotations

import streamlit as st

from data_sources.orchestrator import DataOrchestrator

# Keyed by `DataSource.name`. When a new source is added, extend here.
SOURCE_DESCRIPTIONS: dict[str, dict[str, str]] = {
    "yfinance": {
        "label": "Yahoo Finance",
        "role": "Primary",
        "cost": "Free · no key",
        "covers": "Quotes · fundamentals · price history",
    },
    "finnhub": {
        "label": "Finnhub",
        "role": "Secondary",
        "cost": "Free tier · 60 req/min",
        "covers": "Company news · earnings calendar",
    },
    "alphavantage": {
        "label": "Alpha Vantage",
        "role": "Tertiary (fallback)",
        "cost": "Free tier · 5 req/min",
        "covers": "Quotes · fundamentals (rarely used)",
    },
}


def _active_names(orch: DataOrchestrator) -> list[str]:
    return [s["name"] for s in orch.status() if s["active"]]


def render_footer(orch: DataOrchestrator) -> None:
    """Small attribution caption — call at the bottom of every view.

    Shows only active sources. If only yfinance is on, it reads
    "Data: Yahoo Finance (free)". With Finnhub too: "Data: Yahoo Finance (free)
    + Finnhub (free tier)".
    """
    active = _active_names(orch)
    if not active:
        return
    parts = []
    for name in active:
        meta = SOURCE_DESCRIPTIONS.get(name)
        if meta is None:
            parts.append(name)
            continue
        parts.append(f"{meta['label']} ({meta['cost'].split(' · ')[0].lower()})")
    st.divider()
    st.caption(
        "Data: " + " + ".join(parts)
        + " · This tool is local-first — nothing leaves your machine except the "
        "API calls themselves."
    )
