"""Thin wrappers around Streamlit caching so TTLs are centralized.

Views should import `cache_quote`, `cache_history`, `cache_fundamentals` rather
than call `st.cache_data` directly. This keeps TTLs consistent and makes it
easy to adjust freshness policy in one place.
"""

from __future__ import annotations

import streamlit as st

QUOTE_TTL_SECONDS = 60          # price / change — 1 min fresh
HISTORY_TTL_SECONDS = 60 * 15   # historical OHLC — 15 min fresh
FUNDAMENTALS_TTL_SECONDS = 60 * 60  # P/E, market cap, etc. — 1 hour fresh
COMPANY_INFO_TTL_SECONDS = 60 * 60 * 24  # name / sector / description — 1 day
NEWS_TTL_SECONDS = 60 * 10      # news feed — 10 min fresh
EARNINGS_TTL_SECONDS = 60 * 60 * 6  # earnings calendar — 6 hours fresh


def cache_quote(func):
    return st.cache_data(ttl=QUOTE_TTL_SECONDS, show_spinner=False)(func)


def cache_history(func):
    return st.cache_data(ttl=HISTORY_TTL_SECONDS, show_spinner=False)(func)


def cache_fundamentals(func):
    return st.cache_data(ttl=FUNDAMENTALS_TTL_SECONDS, show_spinner=False)(func)


def cache_company_info(func):
    return st.cache_data(ttl=COMPANY_INFO_TTL_SECONDS, show_spinner=False)(func)


def cache_news(func):
    return st.cache_data(ttl=NEWS_TTL_SECONDS, show_spinner=False)(func)


def cache_earnings(func):
    return st.cache_data(ttl=EARNINGS_TTL_SECONDS, show_spinner=False)(func)
