"""Overview tab — watchlist at a glance with market context.

Layout:
1. **Market context strip** — SPY + QQQ benchmarks (day %, YTD %). Shows
   Roula whether her watchlist is moving with the market or independently.
2. **Watchlist table** — sortable numeric columns, inline 1M sparkline,
   52W position progress bar, volume vs average ratio.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import pandas as pd
import streamlit as st

from config.settings import Settings
from config.theme import callout, page_header, section_label
from data_sources.orchestrator import DataOrchestrator
from lib.cache import cache_fundamentals, cache_history, cache_quote
from lib.formatting import format_pct, format_price
from lib.insights import (
    BENCHMARK_QQQ,
    BENCHMARK_SPY,
    fifty_two_week_position,
    volume_badge,
    volume_ratio,
)
from lib.parallel import fetch_all
from lib.timeframes import SPARKLINE_INTERVAL, SPARKLINE_PERIOD


@cache_quote
def _quote(_orch: DataOrchestrator, ticker: str):
    return _orch.get_quote(ticker)


@cache_fundamentals
def _fundamentals(_orch: DataOrchestrator, ticker: str):
    return _orch.get_fundamentals(ticker)


@cache_history
def _sparkline_series(_orch: DataOrchestrator, ticker: str) -> Optional[List[float]]:
    df = _orch.get_history(ticker, period=SPARKLINE_PERIOD, interval=SPARKLINE_INTERVAL)
    if df is None or df.empty:
        return None
    return [float(x) for x in df["Close"].tolist()]


@cache_history
def _ytd_pct(_orch: DataOrchestrator, ticker: str) -> Optional[float]:
    df = _orch.get_history(ticker, period="ytd", interval="1d")
    if df is None or df.empty or "Close" not in df.columns:
        return None
    first = df["Close"].iloc[0]
    last = df["Close"].iloc[-1]
    if first is None or first == 0 or pd.isna(first) or pd.isna(last):
        return None
    return float(((last - first) / first) * 100.0)


def _render_benchmark_strip(orch: DataOrchestrator) -> None:
    """SPY + QQQ as market context — helps Roula see if watchlist moves
    are market-wide or idiosyncratic."""
    benchmarks: List[Tuple[str, str]] = [
        (BENCHMARK_SPY, "S&P 500"),
        (BENCHMARK_QQQ, "Nasdaq-100"),
    ]
    cols = st.columns(len(benchmarks))
    for i, (symbol, label) in enumerate(benchmarks):
        q = _quote(orch, symbol) or {}
        price = q.get("price")
        change_pct = q.get("change_pct")
        ytd = _ytd_pct(orch, symbol)
        with cols[i]:
            day_str = format_pct(change_pct) if change_pct is not None else "—"
            ytd_str = format_pct(ytd) if ytd is not None else "—"
            price_str = format_price(price) if price is not None else "—"
            st.metric(
                label=f"{symbol} · {label}",
                value=price_str,
                delta=f"{day_str} today · {ytd_str} YTD",
                delta_color="normal" if (change_pct or 0) >= 0 else "inverse",
                help="Benchmark context. Compare your watchlist tickers' performance against this.",
            )


def render(settings: Settings, orch: DataOrchestrator) -> None:
    page_header(
        "Overview",
        f"Market context on top, then your {len(settings.tickers)}-ticker watchlist. "
        f"Prices cached up to 60 seconds — hit Refresh in the sidebar for fresh quotes.",
    )

    # ---- Markets section ----
    # Market context first — so Roula reads "market is up 0.8%" before she reads
    # any individual ticker and can calibrate her reaction.
    section_label("Markets", icon="🌐", tone="accent")
    with st.spinner("Loading market context..."):
        _render_benchmark_strip(orch)

    if not settings.tickers:
        st.info(
            "No tickers configured. Edit `config/tickers.yaml` or say to your "
            "agent: *\"Add TSLA to my watchlist.\"*"
        )
        return

    # ---- Watchlist section ----
    st.markdown("<div style='margin:1.25rem 0'></div>", unsafe_allow_html=True)
    section_label("Your watchlist", icon="👁", tone="cool")
    st.caption(
        "Click any column header to sort. Trend is 30 trading days of closes; "
        "52W Pos is today's price within the yearly range."
    )

    with st.spinner("Loading watchlist..."):
        symbols = [t.symbol for t in settings.tickers]
        quotes = fetch_all(symbols, lambda s: _quote(orch, s))
        fundamentals = fetch_all(symbols, lambda s: _fundamentals(orch, s))
        sparks = fetch_all(symbols, lambda s: _sparkline_series(orch, s))

        rows = []
        for t in settings.tickers:
            q = quotes.get(t.symbol) or {}
            f = fundamentals.get(t.symbol) or {}
            spark = sparks.get(t.symbol)
            mc = f.get("market_cap")
            vol = q.get("volume")
            avg_vol = q.get("avg_volume")
            vr = volume_ratio(vol, avg_vol)
            pos = fifty_two_week_position(
                q.get("price"),
                f.get("fifty_two_week_low"),
                f.get("fifty_two_week_high"),
            )
            rows.append(
                {
                    "Ticker": t.symbol,
                    "Name": t.name or t.symbol,
                    "Trend (1M)": spark,
                    "Price": q.get("price"),
                    "Day %": q.get("change_pct"),
                    "52W Pos": pos,
                    "Vol/Avg": vr,
                    "Vol Flag": volume_badge(vr),
                    "Market Cap ($B)": (mc / 1_000_000_000.0) if mc else None,
                    "P/E": f.get("pe_ratio"),
                }
            )

    df = pd.DataFrame(rows)

    if df["Price"].isna().all():
        st.error(
            "Could not fetch prices for any ticker. yfinance may be temporarily "
            "unavailable, or your network is offline. Hit the Refresh button in "
            "the sidebar to try again."
        )
        return

    st.dataframe(
        df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker", width="small"),
            "Name": st.column_config.TextColumn("Name", width="medium"),
            "Trend (1M)": st.column_config.LineChartColumn(
                "Trend (1M)",
                help="30 trading days of closing prices",
                width="small",
            ),
            "Price": st.column_config.NumberColumn(
                "Price",
                format="$%.2f",
                help="Click header to sort",
            ),
            "Day %": st.column_config.NumberColumn(
                "Day %",
                format="%+.2f%%",
                help="Intraday change — positive or negative",
            ),
            "52W Pos": st.column_config.ProgressColumn(
                "52W Pos",
                format="%.0f%%",
                min_value=0.0,
                max_value=1.0,
                help="Where today's price sits in the 52-week range (0% = at yearly low, 100% = at yearly high)",
            ),
            "Vol/Avg": st.column_config.NumberColumn(
                "Vol/Avg",
                format="%.2fx",
                help="Today's volume as a multiple of the average. Above 2x = unusual activity.",
            ),
            "Vol Flag": st.column_config.TextColumn(
                "🔥",
                help="🔥 = unusual volume (>2x avg), 📊 = heavy, 💤 = quiet",
                width="small",
            ),
            "Market Cap ($B)": st.column_config.NumberColumn(
                "Market Cap ($B)",
                format="%.2f",
                help="Market capitalization in billions USD",
            ),
            "P/E": st.column_config.NumberColumn(
                "P/E",
                format="%.2f",
                help="Trailing twelve months price-to-earnings ratio",
            ),
        },
    )

    # ---- Movers section ----
    # Biggest mover callout — surfaces the headline intraday move rather than
    # making Roula eyeball the table. Uses absolute magnitude of Day %.
    movers = [
        (r["Ticker"], r["Day %"], r.get("Vol/Avg"))
        for r in rows
        if r.get("Day %") is not None
    ]
    if movers:
        st.markdown("<div style='margin:1.25rem 0'></div>", unsafe_allow_html=True)
        top = max(movers, key=lambda m: abs(m[1]))
        sym, pct, vr = top
        if pct > 0:
            direction, tone, icon = "up", "gain", "🚀"
        elif pct < 0:
            direction, tone, icon = "down", "loss", "⬇"
        else:
            direction, tone, icon = "flat", "muted", "•"
        vol_note = ""
        if vr is not None and vr >= 2.0:
            vol_note = f" on <strong>{vr:.1f}× average volume</strong> — unusual"
        callout(
            heading="Biggest mover today",
            icon=icon,
            tone=tone,
            body=(
                f"<strong>{sym}</strong> is {direction} "
                f"<strong>{abs(pct):.2f}%</strong>{vol_note}. "
                "Open the <strong>Detail</strong> tab for the chart, news, "
                "and upcoming earnings."
            ),
        )
