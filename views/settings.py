"""Settings tab — READ-ONLY key status + copyable agent prompts.

Per PRD blocker #2 decision: the Settings UI NEVER writes to .env. All
.env mutations go through the user's Claude Code agent, not the Streamlit
app. This is load-bearing — the §5.6 hard-cap guardrail only holds if the
UI can't raise the cap on its own.

This tab shows:
- Detected-key status for every supported key (✓ present / ✗ missing)
- Current Anthropic budget cap + rate limit (read from .env)
- Copyable prompts she pastes into her Claude Code agent to add / update keys
- Watchlist listing (read-only; editing happens via YAML or via agent prompts)
"""

from __future__ import annotations

import streamlit as st

from config.settings import Settings
from config.theme import page_header, section_label
from data_sources.orchestrator import DataOrchestrator


def _status_row(label: str, present: bool, unlock_hint: str) -> None:
    icon = "✅" if present else "◻️"
    status = "Configured" if present else "Not configured"
    col1, col2, col3 = st.columns([2, 1, 4])
    with col1:
        st.markdown(f"**{label}**")
    with col2:
        st.markdown(f"{icon} {status}")
    with col3:
        st.caption(unlock_hint)


def render(settings: Settings, orch: DataOrchestrator) -> None:
    page_header(
        "Settings",
        "Read-only status + copyable agent prompts. All API key changes happen through "
        "your Claude Code agent — this tab never writes to .env on its own.",
    )

    section_label("API keys", icon="🔑", tone="accent")
    _status_row(
        "yfinance",
        present=True,
        unlock_hint="Primary data source. No key required — always active.",
    )
    _status_row(
        "Finnhub",
        present=settings.has_finnhub,
        unlock_hint="Unlocks news + earnings calendar. Free tier: 60 calls/min.",
    )
    _status_row(
        "Alpha Vantage",
        present=settings.has_alphavantage,
        unlock_hint="Backup fundamentals. Free tier: 25 calls/day.",
    )
    _status_row(
        "Anthropic (Claude)",
        present=settings.has_anthropic,
        unlock_hint="Unlocks AI briefings (Phase 4). Default budget: $5/month.",
    )

    st.divider()

    section_label("Prompts to add or update keys", icon="💬", tone="muted")
    st.caption("Copy a line, paste it to your agent in VS Code, and follow its instructions.")

    prompts = {
        "Add Finnhub key": "Help me add my Finnhub API key to the project.",
        "Add Alpha Vantage key": "Help me add my Alpha Vantage API key to the project.",
        "Add Claude (Anthropic) key": "Help me add my Claude API key so I can get AI briefings.",
        "Raise the Anthropic monthly budget": (
            "Raise ANTHROPIC_MONTHLY_BUDGET_USD in my .env to $10.00. "
            "Explain the tradeoff before you change it."
        ),
    }
    for title, prompt in prompts.items():
        st.markdown(f"**{title}**")
        st.code(prompt, language="text")

    st.divider()

    section_label("Anthropic budget (read-only)", icon="💰", tone="warn")
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Monthly cap", f"${settings.anthropic_monthly_budget_usd:.2f}")
    with col_b:
        st.metric(
            "Min time between briefings",
            f"{settings.anthropic_min_minutes_between_briefings} min",
        )
    st.caption(
        "Edit these by asking your agent to update `.env`. The Streamlit app "
        "never writes to `.env` on its own."
    )

    st.divider()

    section_label("Watchlist", icon="📋", tone="cool")
    if settings.tickers:
        for t in settings.tickers:
            note = f" — {t.note}" if t.note else ""
            st.markdown(f"- **{t.symbol}** · {t.name}{note}")
    else:
        st.info("No tickers configured.")
    st.caption(
        "To change the watchlist, say to your agent: *\"Add TSLA to my watchlist\"* "
        "or *\"Remove USDPHP from my watchlist.\"*"
    )

    st.divider()

    section_label("Data source cascade", icon="🔀", tone="purple")
    for source in orch.status():
        icon = "🟢" if source["active"] else "⚪"
        st.markdown(f"{icon} **{source['name']}** — {'active' if source['active'] else 'not configured'}")
