"""Number and string formatting helpers used across views."""

from __future__ import annotations

from typing import Optional

EM_DASH = "—"


def format_money(value: Optional[float], decimals: int = 2) -> str:
    """Format a number as USD with T/B/M/K suffixes."""
    if value is None:
        return EM_DASH
    try:
        v = float(value)
    except (TypeError, ValueError):
        return EM_DASH
    abs_v = abs(v)
    if abs_v >= 1e12:
        return f"${v / 1e12:.{decimals}f}T"
    if abs_v >= 1e9:
        return f"${v / 1e9:.{decimals}f}B"
    if abs_v >= 1e6:
        return f"${v / 1e6:.{decimals}f}M"
    if abs_v >= 1e3:
        return f"${v / 1e3:.{decimals}f}K"
    return f"${v:,.{decimals}f}"


def format_price(value: Optional[float]) -> str:
    if value is None:
        return EM_DASH
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return EM_DASH


def format_pct(value: Optional[float], signed: bool = True) -> str:
    """Format a decimal percentage. Input can be 0.0178 or 1.78 — see `as_fraction`."""
    if value is None:
        return EM_DASH
    try:
        v = float(value)
    except (TypeError, ValueError):
        return EM_DASH
    return f"{v:+.2f}%" if signed else f"{v:.2f}%"


def format_ratio(value: Optional[float], decimals: int = 2) -> str:
    if value is None:
        return EM_DASH
    try:
        return f"{float(value):.{decimals}f}"
    except (TypeError, ValueError):
        return EM_DASH


def format_volume(value: Optional[float]) -> str:
    if value is None:
        return EM_DASH
    try:
        v = float(value)
    except (TypeError, ValueError):
        return EM_DASH
    abs_v = abs(v)
    if abs_v >= 1e9:
        return f"{v / 1e9:.2f}B"
    if abs_v >= 1e6:
        return f"{v / 1e6:.2f}M"
    if abs_v >= 1e3:
        return f"{v / 1e3:.2f}K"
    return f"{int(v):,}"


def delta_color(change: Optional[float]) -> str:
    """Return 'normal' / 'inverse' / 'off' for Streamlit metric delta_color."""
    if change is None:
        return "off"
    try:
        if float(change) > 0:
            return "normal"
        if float(change) < 0:
            return "inverse"
    except (TypeError, ValueError):
        return "off"
    return "off"


def escape_streamlit_dollars(text: Optional[str]) -> str:
    """Escape `$` so Streamlit's KaTeX doesn't render `$189.49` / `\$ZAR` as math.

    Streamlit's `st.markdown` (and `st.write`, `st.caption`) interprets `$...$`
    as inline LaTeX math. Briefings, news summaries, and company descriptions
    routinely mention prices and $-prefixed tickers; unescaped, they render
    in italic serif. Replace every `$` with `\\$` at display time.

    Idempotent — if the text already has `\\$`, we don't double-escape. This
    matters because the user's briefing might be re-displayed across reruns.
    """
    if text is None:
        return ""
    # Replace $ with \$ — but only if not already escaped. Walk left-to-right
    # so "\$100" stays "\$100" (the preceding backslash protects the $).
    out: list[str] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "$" and (i == 0 or text[i - 1] != "\\"):
            out.append("\\$")
        else:
            out.append(ch)
        i += 1
    return "".join(out)
