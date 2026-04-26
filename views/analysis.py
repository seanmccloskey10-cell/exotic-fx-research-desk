"""Analysis tab — per-stock fundamentals + technicals deep dive.

Post Phase 9 UI polish — layout inspired by Koyfin's security snapshots:

1. **Hero strip** — dense horizontal row at the top with the essentials
   (ticker, price, market cap, P/E, dividend yield, RSI, 52W position).
   Scannable in under a second.
2. **Fundamentals grouped into three purpose-based sections**:
   Valuation · Profitability · Balance Sheet & Risk.
3. **Peer-rank bars** under every metric — replaces the old "peer median: X"
   caption with a visual min→max bar and a color-coded dot showing whether
   the ticker is rich/fair/cheap (or strong/average/weak for profitability).
4. **Technicals section** (unchanged from Phase 7/8) — RSI, MACD, MA overlay.
"""

from __future__ import annotations

import statistics
from typing import Callable, Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components.metric_card import metric_card
from components.peer_rank_bar import peer_rank_bar
from components.sparkline import sparkline
from config.settings import Settings
from config.theme import page_header, section_label
from data_sources.orchestrator import DataOrchestrator
from lib.cache import cache_company_info, cache_fundamentals, cache_history, cache_quote
from lib.formatting import format_money, format_pct, format_price, format_ratio
from lib.insights import fifty_two_week_position
from lib.parallel import fetch_all
from lib.technicals import (
    macd,
    macd_state,
    price_vs_ma,
    rsi,
    rsi_series,
    rsi_state,
    sma,
)

GRID = "#2A2E36"
MA20_COLOR = "#38BDF8"
MA50_COLOR = "#F59E0B"
MA200_COLOR = "#A855F7"
PRICE_COLOR = "#E5E7EB"


@cache_quote
def _quote(_orch: DataOrchestrator, ticker: str):
    return _orch.get_quote(ticker)


@cache_fundamentals
def _fundamentals(_orch: DataOrchestrator, ticker: str):
    return _orch.get_fundamentals(ticker)


@cache_company_info
def _company_info(_orch: DataOrchestrator, ticker: str):
    return _orch.get_company_info(ticker)


@cache_history
def _one_year_history(_orch: DataOrchestrator, ticker: str):
    return _orch.get_history(ticker, period="1y", interval="1d")


# ---------- Peer-context helpers ----------

# Keys we gather peer data for, one per fundamentals metric surfaced in the UI.
_PEER_KEYS = (
    "market_cap",
    "pe_ratio",
    "forward_pe",
    "pb_ratio",
    "eps",
    "beta",
    "profit_margin",
    "debt_to_equity",
    "dividend_yield",
    "roe",
)


def _median(values: list[Optional[float]]) -> Optional[float]:
    """Median of the non-None values. None if all missing."""
    present = [v for v in values if v is not None]
    if not present:
        return None
    return statistics.median(present)


def _collect_peers(
    orch: DataOrchestrator, symbols: list[str], exclude: Optional[str] = None
) -> dict[str, list[Optional[float]]]:
    """Per-metric list of peer values (self excluded).

    Returns dict keyed by metric name with a list of Optional[float] — one
    entry per peer ticker. The peer-rank bar component filters out Nones.
    """
    if len(symbols) <= 1:
        return {k: [] for k in _PEER_KEYS}
    funds_map = fetch_all(symbols, lambda s: _fundamentals(orch, s))
    rows = [funds_map.get(s) or {} for s in symbols if s != exclude]
    return {k: [r.get(k) for r in rows] for k in _PEER_KEYS}


# ---------- MA overlay chart ----------

def _build_ma_overlay(history: pd.DataFrame, ticker: str) -> go.Figure:
    close = history["Close"]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=history.index,
            y=close,
            name="Price",
            mode="lines",
            line=dict(color=PRICE_COLOR, width=1.8),
            hovertemplate="%{x|%Y-%m-%d}: $%{y:.2f}<extra></extra>",
        )
    )
    for window, color, label in (
        (20, MA20_COLOR, "SMA 20"),
        (50, MA50_COLOR, "SMA 50"),
        (200, MA200_COLOR, "SMA 200"),
    ):
        if len(close) < window:
            continue
        ma_series = close.rolling(window).mean()
        fig.add_trace(
            go.Scatter(
                x=history.index,
                y=ma_series,
                name=label,
                mode="lines",
                line=dict(color=color, width=1.2, dash="dot" if window == 200 else "solid"),
                hovertemplate=f"{label}: $%{{y:.2f}}<extra></extra>",
            )
        )
    fig.update_layout(
        height=420,
        margin=dict(l=0, r=0, t=20, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor=GRID),
        yaxis=dict(gridcolor=GRID, tickprefix="$"),
        legend=dict(orientation="h", y=1.05, x=0.5, xanchor="center"),
        hovermode="x unified",
        title=dict(text=f"{ticker} — price vs moving averages", x=0.01, font=dict(size=14)),
    )
    return fig


# ---------- Formatters ----------

def _fmt_decimal_pct(value: Optional[float]) -> str:
    """Fractional input (0.23) → '23.0%'. For profit margin, ROE, dividend yield."""
    if value is None:
        return "—"
    return format_pct(value * 100.0, signed=False)


def _fmt_money_compact(value: Optional[float]) -> str:
    return format_money(value, decimals=2)


def _fmt_ratio_2(value: Optional[float]) -> str:
    return format_ratio(value, decimals=2)


def _fmt_price(value: Optional[float]) -> str:
    return format_price(value)


# ---------- Metric renderer ----------

def _render_metric_with_rank(
    col,
    label: str,
    value: Optional[float],
    value_str: str,
    peers: list[Optional[float]],
    higher_is_better: Optional[bool],
    format_fn: Callable[[Optional[float]], str],
) -> None:
    """Metric card + peer-rank bar stacked vertically in one column slot."""
    with col:
        metric_card(label, value_str)
        peer_rank_bar(
            value=value,
            peers=peers,
            higher_is_better=higher_is_better,
            format_fn=format_fn,
        )


# ---------- Render ----------

def render(settings: Settings, orch: DataOrchestrator) -> None:
    page_header(
        "Analysis",
        "Pick a ticker for a deep dive. Hero strip gives the at-a-glance take; "
        "grouped sections unpack valuation, profitability, balance-sheet health, "
        "and technical state with peer-rank bars showing where this ticker sits.",
    )

    if not settings.tickers:
        st.info(
            "No tickers configured. Say to your agent: *\"Add CRDO to my watchlist.\"*"
        )
        return

    # ---- Ticker selector ----
    symbols = [t.symbol for t in settings.tickers]
    labels = {
        t.symbol: f"{t.symbol} — {t.name}" if t.name else t.symbol
        for t in settings.tickers
    }
    selected = st.selectbox(
        "Ticker",
        options=symbols,
        format_func=lambda s: labels.get(s, s),
        key="analysis_ticker",
    )

    with st.spinner(f"Loading {selected}..."):
        q = _quote(orch, selected) or {}
        f = _fundamentals(orch, selected) or {}
        info = _company_info(orch, selected) or {}
        history = _one_year_history(orch, selected)
        peers = _collect_peers(orch, symbols, exclude=selected)

    price = q.get("price")
    change_pct = q.get("change_pct")
    # Pre-compute a few hero-strip values that depend on both quote + history.
    rsi_val = rsi(history["Close"], period=14) if history is not None and not history.empty else None
    pos_52w = fifty_two_week_position(
        price, f.get("fifty_two_week_low"), f.get("fifty_two_week_high")
    )

    # =====================================================================
    # Ticker header — name block above the hero strip so the metric cards
    # below sit on a single aligned baseline.
    # =====================================================================
    name = info.get("name") or selected
    sector = info.get("sector")
    industry = info.get("industry")
    st.markdown(
        f"<div style='line-height:1.15; margin-bottom:8px'>"
        f"<div style='font-size:1.75rem; font-weight:600; letter-spacing:-0.015em'>{selected}</div>"
        f"<div style='color:#A0A0A0; font-size:0.9rem; margin-top:2px'>"
        f"{name}"
        f"{' · ' + sector if sector else ''}"
        f"{' / ' + industry if industry else ''}"
        f"</div></div>",
        unsafe_allow_html=True,
    )

    # =====================================================================
    # Hero strip — six equal metric cards on one aligned baseline
    # =====================================================================
    hero_cols = st.columns(6)
    with hero_cols[0]:
        metric_card(
            label="Price",
            value=_fmt_price(price),
            delta=format_pct(change_pct) if change_pct is not None else None,
            delta_raw=change_pct,
        )
    with hero_cols[1]:
        metric_card("Market Cap", _fmt_money_compact(f.get("market_cap")))
    with hero_cols[2]:
        metric_card("P/E (TTM)", _fmt_ratio_2(f.get("pe_ratio")))
    with hero_cols[3]:
        metric_card("Dividend Yield", _fmt_decimal_pct(f.get("dividend_yield")))
    with hero_cols[4]:
        metric_card(
            "RSI(14)",
            _fmt_ratio_2(rsi_val) if rsi_val is not None else "—",
            delta=rsi_state(rsi_val) if rsi_val is not None else None,
            delta_raw=None,
        )
    with hero_cols[5]:
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

    # =====================================================================
    # Fundamentals — three purpose-based sections
    # =====================================================================
    st.subheader("Fundamentals")
    st.caption(
        "Each card shows the raw value for this ticker; the bar underneath "
        "places it in the range of the rest of your watchlist. Green = "
        "favorable position for that metric, red = unfavorable, amber = middle."
    )

    # ---- Valuation ----
    section_label("Valuation", tone="accent")
    val_cols = st.columns(5)
    _render_metric_with_rank(
        val_cols[0], "Market Cap",
        f.get("market_cap"), _fmt_money_compact(f.get("market_cap")),
        peers["market_cap"], higher_is_better=None,
        format_fn=_fmt_money_compact,
    )
    _render_metric_with_rank(
        val_cols[1], "P/E (TTM)",
        f.get("pe_ratio"), _fmt_ratio_2(f.get("pe_ratio")),
        peers["pe_ratio"], higher_is_better=False,
        format_fn=_fmt_ratio_2,
    )
    _render_metric_with_rank(
        val_cols[2], "Forward P/E",
        f.get("forward_pe"), _fmt_ratio_2(f.get("forward_pe")),
        peers["forward_pe"], higher_is_better=False,
        format_fn=_fmt_ratio_2,
    )
    _render_metric_with_rank(
        val_cols[3], "P/B",
        f.get("pb_ratio"), _fmt_ratio_2(f.get("pb_ratio")),
        peers["pb_ratio"], higher_is_better=False,
        format_fn=_fmt_ratio_2,
    )
    _render_metric_with_rank(
        val_cols[4], "Dividend Yield",
        f.get("dividend_yield"), _fmt_decimal_pct(f.get("dividend_yield")),
        peers["dividend_yield"], higher_is_better=True,
        format_fn=_fmt_decimal_pct,
    )

    # ---- Profitability ----
    section_label("Profitability", tone="gain")
    prof_cols = st.columns(5)
    _render_metric_with_rank(
        prof_cols[0], "ROE",
        f.get("roe"), _fmt_decimal_pct(f.get("roe")),
        peers["roe"], higher_is_better=True,
        format_fn=_fmt_decimal_pct,
    )
    _render_metric_with_rank(
        prof_cols[1], "Profit Margin",
        f.get("profit_margin"), _fmt_decimal_pct(f.get("profit_margin")),
        peers["profit_margin"], higher_is_better=True,
        format_fn=_fmt_decimal_pct,
    )
    _render_metric_with_rank(
        prof_cols[2], "EPS (TTM)",
        f.get("eps"), _fmt_price(f.get("eps")),
        peers["eps"], higher_is_better=None,  # cross-ticker EPS isn't apples-to-apples
        format_fn=_fmt_price,
    )
    # Two unused slots — left deliberately empty so the row still aligns
    # with Valuation. Streamlit columns render blank when nothing's placed.

    # ---- Balance Sheet & Risk ----
    section_label("Balance sheet & risk", tone="warn")
    bs_cols = st.columns(5)
    _render_metric_with_rank(
        bs_cols[0], "Debt/Equity",
        f.get("debt_to_equity"), _fmt_ratio_2(f.get("debt_to_equity")),
        peers["debt_to_equity"], higher_is_better=False,
        format_fn=_fmt_ratio_2,
    )
    _render_metric_with_rank(
        bs_cols[1], "Beta",
        f.get("beta"), _fmt_ratio_2(f.get("beta")),
        peers["beta"], higher_is_better=None,  # volatility preference is user-specific
        format_fn=_fmt_ratio_2,
    )
    # Static 52W range panel — not a peer-comparable metric, just context.
    # Append an empty spacer div so these cards align vertically with the
    # peer-rank-bar cards next to them in the same row.
    _spacer = "<div class='erd-rank-spacer'></div>"
    with bs_cols[2]:
        metric_card(
            "52W High",
            _fmt_price(f.get("fifty_two_week_high")),
        )
        st.markdown(_spacer, unsafe_allow_html=True)
    with bs_cols[3]:
        metric_card(
            "52W Low",
            _fmt_price(f.get("fifty_two_week_low")),
        )
        st.markdown(_spacer, unsafe_allow_html=True)

    st.markdown("<div style='margin:1.25rem 0'></div>", unsafe_allow_html=True)

    # =====================================================================
    # Technicals
    # =====================================================================
    st.subheader("Technicals")
    st.caption(
        "RSI, MACD, and moving averages computed from 1-year daily history. "
        "Technicals are context — use them alongside the fundamental picture above."
    )

    if history is None or history.empty:
        st.warning(
            f"Could not load price history for **{selected}**. Technicals need "
            "enough daily candles — try Refresh in the sidebar."
        )
        return

    close = history["Close"]
    rsi_label = rsi_state(rsi_val)
    macd_vals = macd(close) or {}
    macd_cross = macd_state(close)
    ma20 = sma(close, 20)
    ma50 = sma(close, 50)
    ma200 = sma(close, 200)
    price_for_ma = price or (float(close.iloc[-1]) if not close.empty else None)
    pct_vs_200 = price_vs_ma(price_for_ma, ma200)

    cols = st.columns(4)
    with cols[0]:
        metric_card(
            "RSI(14)",
            format_ratio(rsi_val, decimals=1) if rsi_val is not None else "—",
            delta=rsi_label if rsi_val is not None else None,
            delta_raw=None,
        )
        rsi_full = rsi_series(close, period=14)
        if rsi_full is not None:
            fig_spark = sparkline(rsi_full.tail(90).dropna(), height=50)
            if fig_spark is not None:
                st.plotly_chart(
                    fig_spark,
                    use_container_width=True,
                    config={"displayModeBar": False},
                )
                st.caption("RSI — last 90 days")

    with cols[1]:
        macd_val = macd_vals.get("macd")
        hist_val = macd_vals.get("histogram")
        metric_card(
            "MACD line",
            format_ratio(macd_val, decimals=3) if macd_val is not None else "—",
            delta=(f"hist {hist_val:+.3f}" if hist_val is not None else None),
            delta_raw=hist_val,
        )

    with cols[2]:
        direction = macd_cross.get("crossover", "none")
        days = macd_cross.get("days_since_crossover")
        if direction == "bullish":
            cross_value = "Bullish"
            cross_delta = f"{days}d ago" if days is not None else None
            cross_raw = 1.0
        elif direction == "bearish":
            cross_value = "Bearish"
            cross_delta = f"{days}d ago" if days is not None else None
            cross_raw = -1.0
        else:
            cross_value = "No recent crossover"
            cross_delta = None
            cross_raw = None
        metric_card("MACD crossover", cross_value, delta=cross_delta, delta_raw=cross_raw)

    with cols[3]:
        if pct_vs_200 is None:
            metric_card("Price vs 200MA", "—")
        else:
            trend_label = (
                "Uptrend" if pct_vs_200 > 0
                else "Downtrend" if pct_vs_200 < 0
                else "At MA"
            )
            metric_card(
                "Price vs 200MA",
                format_pct(pct_vs_200 * 100, signed=True),
                delta=trend_label,
                delta_raw=pct_vs_200,
            )

    fig = _build_ma_overlay(history, selected)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    ma_cols = st.columns(3)
    with ma_cols[0]:
        metric_card("SMA 20", _fmt_price(ma20))
    with ma_cols[1]:
        metric_card("SMA 50", _fmt_price(ma50))
    with ma_cols[2]:
        metric_card("SMA 200", _fmt_price(ma200))
