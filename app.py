"""Streamlit entry point — FX Research Desk.

Launch:
    streamlit run app.py

Or, via the scripts that also manage the .streamlit.pid lifecycle:
    python scripts/start_dashboard.py
    python scripts/stop_dashboard.py

Tabs: Overview · Detail · AI Brief · Analysis · Patterns (Educational) · Settings.
"""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from config.settings import Settings, load_settings
from config.theme import apply_theme
from data_sources.orchestrator import DataOrchestrator, build_default_orchestrator
from lib.formatting import format_pct, format_price
from lib.market_hours import current_status
from lib.provenance import SOURCE_DESCRIPTIONS, render_footer
from views import analysis, briefing, overview, patterns, settings as settings_view, ticker_detail


st.set_page_config(
    page_title="FX Research Desk",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme()


@st.cache_resource
def _orchestrator() -> DataOrchestrator:
    return build_default_orchestrator()


@st.cache_resource
def _settings() -> Settings:
    return load_settings()


def _sidebar(settings: Settings, orch: DataOrchestrator) -> None:
    st.sidebar.title("FX Research Desk")
    st.sidebar.caption("Local-first. Your data, your machine.")

    # Track the last refresh timestamp across reruns so Roula can see data
    # staleness at a glance. Updated on refresh-button click.
    if "last_refresh" not in st.session_state:
        st.session_state["last_refresh"] = datetime.now()

    # Market session indicator — pulsing dot when open, otherwise static.
    market = current_status()
    dot_class = {
        "regular": "open",
        "pre": "pre",
        "after": "after",
        "closed": "closed",
    }.get(market.state, "unknown")
    st.sidebar.markdown(
        f'<div class="erd-market-status" title="US stock market session">'
        f'<span class="dot {dot_class}"></span>'
        f'<span class="label">NYSE {market.label}</span>'
        f'<span class="time">{market.et_time}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.sidebar.subheader("Watchlist")
    for t in settings.tickers:
        q = orch.get_quote(t.symbol) or {}
        price = q.get("price")
        change_pct = q.get("change_pct") or 0
        if change_pct > 0:
            row_cls, color = "up", "#16A34A"
        elif change_pct < 0:
            row_cls, color = "down", "#DC2626"
        else:
            row_cls, color = "flat", "#A0A0A0"
        pct_str = format_pct(change_pct) if q.get("change_pct") is not None else "—"
        st.sidebar.markdown(
            f'<div class="erd-sb-watch {row_cls}">'
            f'<span class="tic">{t.symbol}</span>'
            f'<span>'
            f'<span class="px">{format_price(price)}</span>'
            f'<span class="pct" style="color:{color}">{pct_str}</span>'
            f'</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    if st.sidebar.button("🔄 Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.session_state["last_refresh"] = datetime.now()
        st.rerun()

    last = st.session_state["last_refresh"]
    mins_ago = int((datetime.now() - last).total_seconds() // 60)
    if mins_ago < 1:
        staleness = "just now"
    elif mins_ago == 1:
        staleness = "1 min ago"
    elif mins_ago < 60:
        staleness = f"{mins_ago} min ago"
    else:
        staleness = f"{mins_ago // 60} hr ago"
    st.sidebar.caption(f"Last refreshed {staleness} · {last.strftime('%H:%M')}")

    st.sidebar.subheader("Data sources")
    for source in orch.status():
        active = source["active"]
        meta = SOURCE_DESCRIPTIONS.get(source["name"], {})
        label = meta.get("label", source["name"])
        role = meta.get("role", "")
        cost = meta.get("cost", "")
        covers = meta.get("covers", "")
        state_cls = "active" if active else "inactive"
        st.sidebar.markdown(
            f'<div class="erd-sb-source {state_cls}">'
            f'<span class="src-dot"></span>'
            f'<span class="src-label">{label}</span>'
            f'<span class="src-role">{role if active else "Off"}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if active and covers:
            st.sidebar.caption(f"{covers} · {cost}")
        elif not active and cost:
            st.sidebar.caption(f"Not configured · {cost}")


def main() -> None:
    settings = _settings()
    orch = _orchestrator()

    _sidebar(settings, orch)

    tab_overview, tab_detail, tab_brief, tab_analysis, tab_patterns, tab_settings = st.tabs(
        ["Overview", "Detail", "AI Brief", "Analysis", "Patterns (Educational)", "Settings"]
    )

    with tab_overview:
        overview.render(settings, orch)
        render_footer(orch)
    with tab_detail:
        ticker_detail.render(settings, orch)
        render_footer(orch)
    with tab_brief:
        briefing.render(settings, orch)
        render_footer(orch)
    with tab_analysis:
        analysis.render(settings, orch)
        render_footer(orch)
    with tab_patterns:
        patterns.render(settings, orch)
    with tab_settings:
        settings_view.render(settings, orch)
        render_footer(orch)


if __name__ == "__main__":
    main()
