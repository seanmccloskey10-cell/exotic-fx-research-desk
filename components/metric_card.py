"""Metric card — Streamlit metric with formatted value + delta coloring.

Phase 1 uses Streamlit's built-in st.metric. Phase 2 may replace this with
a fully custom card component; the signature below will stay stable.
"""

from __future__ import annotations

from typing import Optional

import streamlit as st

from lib.formatting import delta_color


def metric_card(
    label: str,
    value: str,
    delta: Optional[str] = None,
    delta_raw: Optional[float] = None,
    help_text: Optional[str] = None,
) -> None:
    """Render a metric card.

    Args:
        label: Short metric name, e.g. "Market Cap".
        value: Pre-formatted value string, e.g. "$6.10B".
        delta: Pre-formatted delta string, e.g. "+1.78%". Pass None for no delta.
        delta_raw: Raw numeric delta used to pick color (positive/negative).
        help_text: Tooltip shown on hover.
    """
    st.metric(
        label=label,
        value=value,
        delta=delta,
        delta_color=delta_color(delta_raw) if delta is not None else "off",
        help=help_text,
    )
