"""Detail tab — per-ticker view with dropdown selector.

Per PRD blocker #1 decision: one Detail tab with a dropdown, not a tab per
ticker. Keeps the UI stable when the user adds / removes tickers.

Post Phase 9 visual upgrade: page header rule, rich ticker header block,
hero strip, and grouped metric sections (Trading activity / Valuation /
52W range) instead of the flat 10-card wall.
"""

from __future__ import annotations

import streamlit as st

from components.candlestick_chart import candlestick_chart
from components.metric_card import metric_card
from config.settings import Settings
from config.theme import page_header, section_label
from data_sources.orchestrator import DataOrchestrator
from lib.cache import (
    cache_company_info,
    cache_earnings,
    cache_fundamentals,
    cache_history,
    cache_news,
    cache_quote,
)
from lib.formatting import (
    escape_streamlit_dollars,
    format_money,
    format_pct,
    format_price,
    format_ratio,
    format_volume,
)
from lib.insights import fifty_two_week_position
from lib.timeframes import DEFAULT_INDEX, TIMEFRAMES


@cache_quote
def _quote(_orch: DataOrchestrator, ticker: str):
    return _orch.get_quote(ticker)


@cache_fundamentals
def _fundamentals(_orch: DataOrchestrator, ticker: str):
    return _orch.get_fundamentals(ticker)


@cache_history
def _history(_orch: DataOrchestrator, ticker: str, period: str, interval: str):
    return _orch.get_history(ticker, period=period, interval=interval)


@cache_company_info
def _company_info(_orch: DataOrchestrator, ticker: str):
    return _orch.get_company_info(ticker)


@cache_news
def _news(_orch: DataOrchestrator, ticker: str):
    return _orch.get_news(ticker)


@cache_earnings
def _earnings(_orch: DataOrchestrator, ticker: str):
    return _orch.get_earnings(ticker)


def _render_ticker_header(selected: str, info: dict) -> None:
    """Rich header block with ticker symbol + company name + sector chain."""
    name = info.get("name") or selected
    sector = info.get("sector")
    industry = info.get("industry")
    sector_line = (
        f"{name}"
        + (f" · {sector}" if sector else "")
        + (f" / {industry}" if industry else "")
    )
    st.markdown(
        f"<div style='line-height:1.15; margin-bottom:10px'>"
        f"<div style='font-size:1.75rem; font-weight:600; letter-spacing:-0.015em'>{selected}</div>"
        f"<div style='color:#A0A0A0; font-size:0.9rem; margin-top:2px'>{sector_line}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def render(settings: Settings, orch: DataOrchestrator) -> None:
    page_header(
        "Detail",
        "Price history, company profile, recent news and upcoming earnings for a single ticker.",
    )

    if not settings.tickers:
        st.info(
            "No pairs configured. Say to your agent: *\"Add USDPLN to my watchlist.\"*"
        )
        return

    symbols = [t.symbol for t in settings.tickers]
    labels = {
        t.symbol: f"{t.symbol} — {t.name}" if t.name else t.symbol
        for t in settings.tickers
    }

    selected = st.selectbox(
        "Ticker",
        options=symbols,
        format_func=lambda s: labels.get(s, s),
        key="detail_ticker",
    )

    with st.spinner(f"Loading {selected}..."):
        q = _quote(orch, selected)
        f = _fundamentals(orch, selected) or {}
        info = _company_info(orch, selected) or {}

    if not q:
        st.error(
            f"Could not fetch a quote for **{selected}**. The ticker may be wrong, "
            "or yfinance may be temporarily unavailable. Try Refresh in the sidebar."
        )
        return

    # --- Ticker header block ---
    _render_ticker_header(selected, info)

    # --- Hero strip: at-a-glance stats ---
    change_raw = q.get("change_pct")
    pos_52w = fifty_two_week_position(
        q.get("price"), f.get("fifty_two_week_low"), f.get("fifty_two_week_high")
    )
    hero = st.columns(5)
    with hero[0]:
        metric_card(
            label="Price",
            value=format_price(q.get("price")),
            delta=format_pct(change_raw) if change_raw is not None else None,
            delta_raw=change_raw,
        )
    with hero[1]:
        metric_card("Market Cap", format_money(f.get("market_cap")))
    with hero[2]:
        metric_card("P/E (TTM)", format_ratio(f.get("pe_ratio")))
    with hero[3]:
        div = f.get("dividend_yield")
        metric_card(
            "Dividend Yield",
            format_pct(div * 100, signed=False) if div is not None else "—",
        )
    with hero[4]:
        metric_card(
            "52W Position",
            format_pct(pos_52w * 100, signed=False) if pos_52w is not None else "—",
            delta=(
                "Near high"
                if pos_52w is not None and pos_52w >= 0.8
                else "Near low"
                if pos_52w is not None and pos_52w <= 0.2
                else "Mid-range"
                if pos_52w is not None
                else None
            ),
            delta_raw=pos_52w if pos_52w is not None else None,
        )

    st.markdown("<div style='margin:1.25rem 0'></div>", unsafe_allow_html=True)

    # --- Price history — primary surface on this tab ---
    section_label("Price history", icon="📉", tone="accent")
    tf_label = st.radio(
        "Timeframe",
        options=list(TIMEFRAMES.keys()),
        index=DEFAULT_INDEX,
        horizontal=True,
        key=f"tf_{selected}",
        label_visibility="collapsed",
    )
    period, interval = TIMEFRAMES[tf_label]
    with st.spinner(f"Loading {tf_label} chart..."):
        history = _history(orch, selected, period, interval)

    if history is None or history.empty:
        st.info(f"Price history unavailable for the {tf_label} timeframe.")
    else:
        fig = candlestick_chart(history, title=selected)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # --- Trading activity (volume + day range) ---
    section_label("Trading activity", icon="⚡", tone="cool")
    act_cols = st.columns(4)
    with act_cols[0]:
        metric_card("Volume", format_volume(q.get("volume")))
    with act_cols[1]:
        metric_card("Avg Volume", format_volume(q.get("avg_volume")))
    with act_cols[2]:
        day_range = (
            f"{format_price(q.get('day_low'))} – {format_price(q.get('day_high'))}"
            if q.get("day_low") is not None and q.get("day_high") is not None
            else "—"
        )
        metric_card("Day Range", day_range)
    with act_cols[3]:
        roe = f.get("roe")
        metric_card(
            "ROE",
            format_pct(roe * 100, signed=False) if roe is not None else "—",
        )

    # --- 52W range anchors ---
    section_label("52-week range", icon="📏", tone="purple")
    range_cols = st.columns(4)
    with range_cols[0]:
        metric_card("52W High", format_price(f.get("fifty_two_week_high")))
    with range_cols[1]:
        metric_card("52W Low", format_price(f.get("fifty_two_week_low")))
    with range_cols[2]:
        metric_card("P/B", format_ratio(f.get("pb_ratio")))
    with range_cols[3]:
        metric_card("Beta", format_ratio(f.get("beta")))

    # --- Company description ---
    # Always visible — collapsed-by-default hid useful context. Long
    # descriptions still use an expander so the user can tuck them away,
    # but it opens expanded so the text isn't missed on first visit.
    # Escape $ so Streamlit's KaTeX doesn't math-italicize dollar amounts.
    description = info.get("description")
    if description:
        section_label("About", icon="🏢", tone="muted")
        safe_desc = escape_streamlit_dollars(description)
        if len(description) > 280:
            with st.expander(f"About {selected}", expanded=True):
                st.write(safe_desc)
        else:
            st.write(safe_desc)

    # --- News + earnings ---
    st.markdown("<div style='margin:1.25rem 0'></div>", unsafe_allow_html=True)
    col_news, col_earnings = st.columns([3, 2])

    with col_news:
        section_label("Recent news", icon="📰", tone="cool")
        if not settings.has_finnhub:
            st.info(
                "Recent news requires a Finnhub API key. Say to your agent: "
                "*\"Help me add my Finnhub key.\"*"
            )
        else:
            with st.spinner("Loading news..."):
                articles = _news(orch, selected)
            if not articles:
                st.caption("No recent articles from Finnhub for this ticker.")
            else:
                for a in articles:
                    meta_bits = []
                    if a.get("publisher"):
                        meta_bits.append(a["publisher"])
                    if a.get("published_at"):
                        meta_bits.append(a["published_at"].strftime("%Y-%m-%d"))
                    meta = " · ".join(meta_bits) if meta_bits else ""
                    # Escape $ in LLM/publisher-generated text so prices
                    # and $-prefixed tickers don't trigger KaTeX math rendering.
                    title = escape_streamlit_dollars(a.get("title") or "(untitled)")
                    url = a.get("url") or "#"
                    with st.container(border=True):
                        st.markdown(f"**[{title}]({url})**")
                        if meta:
                            st.caption(meta)
                        if a.get("summary"):
                            raw = a["summary"][:200] + ("…" if len(a["summary"]) > 200 else "")
                            st.caption(escape_streamlit_dollars(raw))

    with col_earnings:
        section_label("Upcoming earnings", icon="🗓", tone="warn")
        if not settings.has_finnhub:
            st.info(
                "Earnings calendar requires a Finnhub API key. Say to your agent: "
                "*\"Help me add my Finnhub key.\"*"
            )
        else:
            with st.spinner("Loading earnings..."):
                e = _earnings(orch, selected)
            if not e or not e.get("next_date"):
                st.caption("No upcoming earnings event in the next 90 days.")
            else:
                when_map = {"bmo": "before the open", "amc": "after the close"}
                when = when_map.get((e.get("time") or "").lower(), "time unconfirmed")
                with st.container(border=True):
                    st.markdown(f"**{e['next_date'].strftime('%A, %d %B %Y')}**")
                    st.caption(when)
                    # Plain text here instead of st.metric — metric cards
                    # force a 124px min-height and bloat the container.
                    if e.get("eps_estimate") is not None:
                        st.markdown(
                            f"<div style='margin-top:6px'><span style='color:#A0A0A0; "
                            f"font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em;'>"
                            f"EPS estimate</span><br>"
                            f"<span style='font-weight:600; font-size:1.05rem;'>"
                            f"{format_ratio(e['eps_estimate'])}</span></div>",
                            unsafe_allow_html=True,
                        )
                    if e.get("revenue_estimate") is not None:
                        st.markdown(
                            f"<div style='margin-top:8px'><span style='color:#A0A0A0; "
                            f"font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em;'>"
                            f"Revenue estimate</span><br>"
                            f"<span style='font-weight:600; font-size:1.05rem;'>"
                            f"{format_money(e['revenue_estimate'])}</span></div>",
                            unsafe_allow_html=True,
                        )
