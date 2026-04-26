"""Dark theme — typography, spacing, and custom card styling.

The base dark theme is declared in `.streamlit/config.toml` (Streamlit loads
that automatically at app start). This module adds a CSS injection pass
for the details Streamlit's built-in theme doesn't cover:

- System font stack (Segoe UI Variable on Windows, -apple-system on macOS)
- Tabular numerics in tables and metrics so columns line up
- Bordered metric cards with subtle surface color
- Tighter heading weights + letter-spacing
- Sidebar separation + price line typography
- Small-caps section labels (`section_label()`)
- Page-header block (`page_header()`)
- Pulse animation for live-market indicator
"""

from __future__ import annotations

from typing import Optional

import streamlit as st

COLORS = {
    "gain": "#16A34A",
    "loss": "#DC2626",
    "flat": "#6B7280",
    "accent": "#3B82F6",
    "accent_soft": "#60A5FA",
    "background": "#0E1117",
    "surface": "#1A1D24",
    "surface_alt": "#14171D",
    "surface_elevated": "#1E2230",
    "border": "#2A2E36",
    "border_strong": "#353A45",
    "text": "#FAFAFA",
    "muted": "#A0A0A0",
    "muted_dim": "#6B7280",
}


_CSS = f"""
<style>
/* ---------------------- Typography ---------------------- */
html, body, [class*="css"], [data-testid="stAppViewContainer"] {{
    font-family: "Segoe UI Variable", -apple-system, BlinkMacSystemFont,
                 "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
    -webkit-font-smoothing: antialiased;
}}

/* Tabular numerics wherever numbers appear */
[data-testid="stMetricValue"],
[data-testid="stMetricDelta"],
[data-testid="stDataFrame"] td,
[data-testid="stDataFrame"] th {{
    font-variant-numeric: tabular-nums;
    font-feature-settings: "tnum" 1;
}}

/* Tighten headings */
h1, h2, h3, h4 {{
    font-weight: 600;
    letter-spacing: -0.015em;
}}
h1 {{ font-size: 1.75rem; }}
h2 {{ font-size: 1.35rem; }}
h3 {{ font-size: 1.125rem; }}

/* ---------------------- Page header ---------------------- */
.erd-page-header {{
    margin: -0.5rem 0 1.25rem 0;
    padding-bottom: 0.85rem;
    border-bottom: 1px solid {COLORS["border"]};
    position: relative;
}}
.erd-page-header::after {{
    content: "";
    position: absolute;
    bottom: -1px;
    left: 0;
    width: 60px;
    height: 2px;
    background: {COLORS["accent"]};
    border-radius: 1px;
}}
.erd-page-header h1 {{
    font-size: 1.6rem;
    font-weight: 600;
    margin: 0 0 0.25rem 0;
    letter-spacing: -0.02em;
}}
.erd-page-header .erd-subtitle {{
    color: {COLORS["muted"]};
    font-size: 0.9rem;
    line-height: 1.5;
}}

/* ---------------------- Section labels ---------------------- */
/* Small-caps heading between h3 and body — sits between subheaders and cards.
   Optional icon chip + tone-colored tick. Per-tone overrides below. */
.erd-section-label {{
    margin: 0.5rem 0 0.75rem 0;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid {COLORS["border"]};
    display: flex;
    align-items: center;
    gap: 0.55rem;
}}
.erd-section-label::before {{
    content: "";
    width: 3px;
    height: 1rem;
    background: {COLORS["accent"]};
    border-radius: 2px;
    flex-shrink: 0;
}}
.erd-section-label .erd-section-icon {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 22px;
    height: 22px;
    background: {COLORS["surface_alt"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 5px;
    font-size: 0.8rem;
    flex-shrink: 0;
}}
.erd-section-label .erd-section-text {{
    color: {COLORS["muted"]};
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}}

/* ---------------------- Tone overrides (shared by section_label + callout) ---------------------- */
.erd-tone-accent::before {{ background: {COLORS["accent"]}; }}
.erd-tone-accent .erd-section-icon {{ background: {COLORS["accent"]}20; border-color: {COLORS["accent"]}44; }}
.erd-tone-accent .erd-section-text {{ color: {COLORS["accent_soft"]}; }}

.erd-tone-gain::before {{ background: #10B981; }}
.erd-tone-gain .erd-section-icon {{ background: #10B98120; border-color: #10B98144; }}
.erd-tone-gain .erd-section-text {{ color: #34D399; }}

.erd-tone-loss::before {{ background: #DC2626; }}
.erd-tone-loss .erd-section-icon {{ background: #DC262620; border-color: #DC262644; }}
.erd-tone-loss .erd-section-text {{ color: #F87171; }}

.erd-tone-warn::before {{ background: #F59E0B; }}
.erd-tone-warn .erd-section-icon {{ background: #F59E0B20; border-color: #F59E0B44; }}
.erd-tone-warn .erd-section-text {{ color: #FBBF24; }}

.erd-tone-cool::before {{ background: #06B6D4; }}
.erd-tone-cool .erd-section-icon {{ background: #06B6D420; border-color: #06B6D444; }}
.erd-tone-cool .erd-section-text {{ color: #22D3EE; }}

.erd-tone-purple::before {{ background: #A855F7; }}
.erd-tone-purple .erd-section-icon {{ background: #A855F720; border-color: #A855F744; }}
.erd-tone-purple .erd-section-text {{ color: #C084FC; }}

.erd-tone-muted::before {{ background: {COLORS["muted_dim"]}; }}
.erd-tone-muted .erd-section-icon {{ background: {COLORS["muted_dim"]}22; border-color: {COLORS["muted_dim"]}44; }}
.erd-tone-muted .erd-section-text {{ color: {COLORS["muted"]}; }}

/* ---------------------- Callout ---------------------- */
/* Hero-style highlight block — for punch-line moments like the
   "Biggest mover today" surface. Tone-tinted gradient + icon chip. */
.erd-callout {{
    display: flex;
    align-items: flex-start;
    gap: 14px;
    padding: 16px 20px;
    border-radius: 12px;
    background: linear-gradient(135deg, {COLORS["accent"]}12 0%, {COLORS["surface"]} 60%, {COLORS["surface_alt"]} 100%);
    border: 1px solid {COLORS["border"]};
    border-left: 4px solid {COLORS["accent"]};
    margin: 0.5rem 0 1rem 0;
}}
.erd-callout-icon {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    font-size: 1.15rem;
    background: {COLORS["accent"]}22;
    border: 1px solid {COLORS["accent"]}44;
    border-radius: 10px;
    flex-shrink: 0;
}}
.erd-callout-text {{ flex: 1; min-width: 0; }}
.erd-callout-heading {{
    color: {COLORS["accent_soft"]};
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 4px;
}}
.erd-callout-body {{
    color: {COLORS["text"]};
    font-size: 1rem;
    line-height: 1.55;
}}
.erd-callout-body strong {{ font-weight: 600; }}

/* Tone variants for callout — override border + gradient + icon chip. */
.erd-callout.erd-tone-gain {{
    background: linear-gradient(135deg, #10B98114 0%, {COLORS["surface"]} 60%, {COLORS["surface_alt"]} 100%);
    border-left-color: #10B981;
}}
.erd-callout.erd-tone-gain .erd-callout-icon {{ background: #10B98122; border-color: #10B98144; }}
.erd-callout.erd-tone-gain .erd-callout-heading {{ color: #34D399; }}

.erd-callout.erd-tone-loss {{
    background: linear-gradient(135deg, #DC262614 0%, {COLORS["surface"]} 60%, {COLORS["surface_alt"]} 100%);
    border-left-color: #DC2626;
}}
.erd-callout.erd-tone-loss .erd-callout-icon {{ background: #DC262622; border-color: #DC262644; }}
.erd-callout.erd-tone-loss .erd-callout-heading {{ color: #F87171; }}

.erd-callout.erd-tone-warn {{
    background: linear-gradient(135deg, #F59E0B14 0%, {COLORS["surface"]} 60%, {COLORS["surface_alt"]} 100%);
    border-left-color: #F59E0B;
}}
.erd-callout.erd-tone-warn .erd-callout-icon {{ background: #F59E0B22; border-color: #F59E0B44; }}
.erd-callout.erd-tone-warn .erd-callout-heading {{ color: #FBBF24; }}

.erd-callout.erd-tone-cool {{
    background: linear-gradient(135deg, #06B6D414 0%, {COLORS["surface"]} 60%, {COLORS["surface_alt"]} 100%);
    border-left-color: #06B6D4;
}}
.erd-callout.erd-tone-cool .erd-callout-icon {{ background: #06B6D422; border-color: #06B6D444; }}
.erd-callout.erd-tone-cool .erd-callout-heading {{ color: #22D3EE; }}

.erd-callout.erd-tone-purple {{
    background: linear-gradient(135deg, #A855F714 0%, {COLORS["surface"]} 60%, {COLORS["surface_alt"]} 100%);
    border-left-color: #A855F7;
}}
.erd-callout.erd-tone-purple .erd-callout-icon {{ background: #A855F722; border-color: #A855F744; }}
.erd-callout.erd-tone-purple .erd-callout-heading {{ color: #C084FC; }}

.erd-callout.erd-tone-muted {{
    background: linear-gradient(135deg, {COLORS["muted_dim"]}14 0%, {COLORS["surface"]} 60%, {COLORS["surface_alt"]} 100%);
    border-left-color: {COLORS["muted_dim"]};
}}
.erd-callout.erd-tone-muted .erd-callout-icon {{ background: {COLORS["muted_dim"]}22; border-color: {COLORS["muted_dim"]}44; }}
.erd-callout.erd-tone-muted .erd-callout-heading {{ color: {COLORS["muted"]}; }}

/* ---------------------- Metric cards ---------------------- */
/* min-height is sized to accommodate a card WITH a delta chip, so cards
   without one don't look squat next to cards that have one. flex-column +
   `margin-top: auto` on the delta keeps it pinned to the bottom even when
   the card has extra space above it. No `height: 100%` — we don't want
   cards to stretch into gaps their column has for a peer-rank-bar below. */
[data-testid="stMetric"] {{
    background: linear-gradient(180deg, {COLORS["surface"]} 0%, {COLORS["surface_alt"]} 100%);
    border: 1px solid {COLORS["border"]};
    border-radius: 10px;
    padding: 14px 16px;
    transition: border-color 0.15s ease, transform 0.15s ease;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    min-height: 124px;
    gap: 4px;
}}
[data-testid="stMetric"]:hover {{
    border-color: {COLORS["border_strong"]};
}}
[data-testid="stMetricLabel"] {{
    color: {COLORS["muted"]};
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}}
[data-testid="stMetricValue"] {{
    font-weight: 600;
    font-size: 1.4rem;
    line-height: 1.2;
    /* Allow natural wrapping — e.g. "Day Range $189.49 – $190.50" needs
       two lines in a narrow column. min-height on the card accommodates. */
    word-break: break-word;
}}
[data-testid="stMetricDelta"] {{
    font-size: 0.82rem;
    font-weight: 500;
    margin-top: auto; /* pushes delta to the bottom so rows sit on an aligned baseline */
}}

/* Spacer for bare metric cards sitting next to peer-rank-bar rows — matches
   the bar's vertical footprint so adjacent cards don't look orphaned. */
.erd-rank-spacer {{
    height: 28px;
}}

/* ---------------------- AI Brief — per-section cards ---------------------- */
/* The briefing has six distinct sections (TL;DR · Snapshot · Themes · Risk ·
   Earnings · Questions). Rendering all six identically wastes the
   daily-ritual surface — each one gets its own role-based treatment. */

.erd-bf-root {{
    display: flex;
    flex-direction: column;
    gap: 14px;
}}

.erd-bf-section {{
    background: {COLORS["surface"]};
    border: 1px solid {COLORS["border"]};
    border-left: 4px solid {COLORS["accent"]};
    border-radius: 12px;
    padding: 18px 22px 14px 22px;
    transition: border-color 0.15s ease;
}}

.erd-bf-title {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
    padding-bottom: 8px;
    border-bottom: 1px solid {COLORS["border"]};
}}

.erd-bf-icon {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    font-size: 1rem;
    background: {COLORS["surface_alt"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    flex-shrink: 0;
}}

.erd-bf-heading {{
    color: {COLORS["text"]};
    font-size: 0.82rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}}

/* Body prose styling — consistent across all sections, but overridable. */
.erd-bf-body {{
    color: {COLORS["text"]};
    font-size: 0.93rem;
    line-height: 1.65;
}}
.erd-bf-body p {{ margin: 0.35rem 0 0.6rem 0; }}
.erd-bf-body p:last-child {{ margin-bottom: 0; }}
.erd-bf-body strong {{
    color: {COLORS["text"]};
    font-weight: 600;
}}
.erd-bf-body em {{ color: {COLORS["muted"]}; }}
.erd-bf-body a {{
    color: {COLORS["accent_soft"]};
    text-decoration: none;
    border-bottom: 1px dotted {COLORS["accent_soft"]}88;
}}
.erd-bf-body a:hover {{
    color: {COLORS["accent"]};
    border-bottom-color: {COLORS["accent"]};
}}
.erd-bf-body ul, .erd-bf-body ol {{
    margin: 0.4rem 0 0.6rem 0;
    padding-left: 1.2rem;
}}
.erd-bf-body li {{
    margin: 0.35rem 0;
    padding-left: 0.1rem;
}}
.erd-bf-body code {{
    background: {COLORS["surface_alt"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 4px;
    padding: 1px 6px;
    font-size: 0.85em;
    color: {COLORS["accent_soft"]};
}}
.erd-bf-body table {{
    width: 100%;
    border-collapse: collapse;
    margin: 0.4rem 0;
    font-size: 0.88rem;
    font-variant-numeric: tabular-nums;
}}
.erd-bf-body th {{
    text-align: left;
    color: {COLORS["muted"]};
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 8px 10px;
    border-bottom: 1px solid {COLORS["border_strong"]};
}}
.erd-bf-body td {{
    padding: 8px 10px;
    border-bottom: 1px solid {COLORS["border"]};
}}
.erd-bf-body tr:last-child td {{ border-bottom: none; }}
.erd-bf-body tr:hover td {{ background: {COLORS["surface_alt"]}; }}

/* ---- TL;DR — hero card, accent-tinted, bigger body text ---- */
.erd-bf-tldr {{
    background: linear-gradient(
        135deg,
        {COLORS["accent"]}12 0%,
        {COLORS["surface"]} 60%,
        {COLORS["surface_alt"]} 100%
    );
    border-left: 4px solid {COLORS["accent"]};
    box-shadow: 0 1px 0 {COLORS["accent"]}14 inset;
}}
.erd-bf-tldr .erd-bf-icon {{
    background: {COLORS["accent"]}22;
    border-color: {COLORS["accent"]}44;
}}
.erd-bf-tldr .erd-bf-heading {{ color: {COLORS["accent_soft"]}; }}
.erd-bf-tldr .erd-bf-body {{
    font-size: 1.02rem;
    line-height: 1.6;
    color: {COLORS["text"]};
}}
.erd-bf-tldr .erd-bf-body p:first-child {{
    font-weight: 500;
}}

/* ---- Snapshot — balanced prose card ---- */
.erd-bf-snapshot {{ border-left-color: #10B981; }}
.erd-bf-snapshot .erd-bf-icon {{
    background: #10B98120;
    border-color: #10B98144;
}}
.erd-bf-snapshot .erd-bf-heading {{ color: #34D399; }}

/* ---- Themes — purple accent, richer bullets ---- */
.erd-bf-themes {{ border-left-color: #A855F7; }}
.erd-bf-themes .erd-bf-icon {{
    background: #A855F720;
    border-color: #A855F744;
}}
.erd-bf-themes .erd-bf-heading {{ color: #C084FC; }}
.erd-bf-themes .erd-bf-body ul {{
    list-style: none;
    padding-left: 0;
}}
.erd-bf-themes .erd-bf-body li {{
    position: relative;
    padding-left: 1.5rem;
    margin: 0.7rem 0;
}}
.erd-bf-themes .erd-bf-body li::before {{
    content: "→";
    position: absolute;
    left: 0;
    top: 0;
    color: #C084FC;
    font-weight: 600;
}}

/* ---- Risk watch — amber left border, soft warning tint ---- */
.erd-bf-risk {{
    border-left-color: #F59E0B;
    background: linear-gradient(
        90deg,
        #F59E0B08 0%,
        {COLORS["surface"]} 40%
    );
}}
.erd-bf-risk .erd-bf-icon {{
    background: #F59E0B20;
    border-color: #F59E0B44;
}}
.erd-bf-risk .erd-bf-heading {{ color: #FBBF24; }}
.erd-bf-risk .erd-bf-body strong:first-child {{
    color: #FBBF24;
}}

/* ---- Earnings — cool accent, emphasis on the table ---- */
.erd-bf-earnings {{ border-left-color: #06B6D4; }}
.erd-bf-earnings .erd-bf-icon {{
    background: #06B6D420;
    border-color: #06B6D444;
}}
.erd-bf-earnings .erd-bf-heading {{ color: #22D3EE; }}
.erd-bf-earnings .erd-bf-body table {{
    background: {COLORS["surface_alt"]};
    border-radius: 8px;
    overflow: hidden;
}}

/* ---- Questions — reflective, italic, muted ---- */
.erd-bf-questions {{
    border-left-color: {COLORS["muted_dim"]};
    background: linear-gradient(
        180deg,
        {COLORS["surface_alt"]} 0%,
        {COLORS["surface"]} 100%
    );
}}
.erd-bf-questions .erd-bf-icon {{
    background: {COLORS["muted_dim"]}22;
    border-color: {COLORS["muted_dim"]}44;
}}
.erd-bf-questions .erd-bf-heading {{ color: {COLORS["muted"]}; }}
.erd-bf-questions .erd-bf-body ol {{
    counter-reset: q-counter;
    list-style: none;
    padding-left: 0;
}}
.erd-bf-questions .erd-bf-body ul {{
    list-style: none;
    padding-left: 0;
}}
.erd-bf-questions .erd-bf-body li {{
    counter-increment: q-counter;
    position: relative;
    padding: 10px 14px 10px 42px;
    margin: 8px 0;
    background: {COLORS["surface_alt"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    font-style: italic;
    color: {COLORS["text"]};
}}
.erd-bf-questions .erd-bf-body li::before {{
    content: counter(q-counter);
    position: absolute;
    left: 14px;
    top: 10px;
    width: 22px;
    height: 22px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: {COLORS["surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 50%;
    font-style: normal;
    font-size: 0.75rem;
    font-weight: 600;
    color: {COLORS["muted"]};
}}

/* ---------------------- Sidebar ---------------------- */
[data-testid="stSidebar"] {{
    background: {COLORS["surface_alt"]};
    border-right: 1px solid {COLORS["border"]};
}}
[data-testid="stSidebar"] h1 {{
    font-size: 1.15rem;
    margin-bottom: 0.1rem;
    font-weight: 600;
    letter-spacing: -0.015em;
}}
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {{
    font-size: 0.7rem;
    color: {COLORS["muted"]};
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-weight: 600;
    margin-top: 0.5rem;
    margin-bottom: 0.4rem;
}}
[data-testid="stSidebar"] hr {{
    margin: 0.75rem 0;
    border-color: {COLORS["border"]};
}}

/* Sidebar watchlist cards */
.erd-sb-watch {{
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    padding: 8px 10px;
    margin-bottom: 4px;
    background: {COLORS["surface"]};
    border: 1px solid {COLORS["border"]};
    border-left: 2px solid {COLORS["border"]};
    border-radius: 6px;
    transition: border-color 0.15s ease;
}}
.erd-sb-watch:hover {{
    border-color: {COLORS["border_strong"]};
}}
.erd-sb-watch.up {{ border-left-color: {COLORS["gain"]}; }}
.erd-sb-watch.down {{ border-left-color: {COLORS["loss"]}; }}
.erd-sb-watch.flat {{ border-left-color: {COLORS["muted_dim"]}; }}
.erd-sb-watch .tic {{
    font-weight: 600;
    font-size: 0.88rem;
    letter-spacing: 0.02em;
}}
.erd-sb-watch .px {{
    font-variant-numeric: tabular-nums;
    font-size: 0.9rem;
    font-weight: 500;
    color: {COLORS["text"]};
}}
.erd-sb-watch .pct {{
    font-variant-numeric: tabular-nums;
    font-size: 0.82rem;
    font-weight: 600;
    margin-left: 8px;
}}

/* Market status row */
.erd-market-status {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 10px;
    background: {COLORS["surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    font-size: 0.82rem;
}}
.erd-market-status .dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}}
.erd-market-status .dot.open {{
    background: {COLORS["gain"]};
    box-shadow: 0 0 0 0 {COLORS["gain"]}99;
    animation: erd-pulse 2s infinite;
}}
.erd-market-status .dot.pre,
.erd-market-status .dot.after {{
    background: #F59E0B;
}}
.erd-market-status .dot.closed {{
    background: {COLORS["muted_dim"]};
}}
.erd-market-status .dot.unknown {{
    background: {COLORS["muted_dim"]};
}}
.erd-market-status .label {{ font-weight: 600; }}
.erd-market-status .time {{
    color: {COLORS["muted"]};
    margin-left: auto;
    font-variant-numeric: tabular-nums;
}}

@keyframes erd-pulse {{
    0% {{ box-shadow: 0 0 0 0 {COLORS["gain"]}80; }}
    70% {{ box-shadow: 0 0 0 6px {COLORS["gain"]}00; }}
    100% {{ box-shadow: 0 0 0 0 {COLORS["gain"]}00; }}
}}

/* Sidebar data-source rows */
.erd-sb-source {{
    padding: 6px 10px;
    margin-bottom: 4px;
    border-radius: 6px;
    font-size: 0.82rem;
    background: {COLORS["surface"]};
    border: 1px solid {COLORS["border"]};
    display: flex;
    align-items: baseline;
    gap: 6px;
}}
.erd-sb-source.inactive {{
    opacity: 0.55;
    background: transparent;
}}
.erd-sb-source .src-dot {{
    width: 7px;
    height: 7px;
    border-radius: 50%;
    flex-shrink: 0;
}}
.erd-sb-source.active .src-dot {{ background: {COLORS["gain"]}; }}
.erd-sb-source.inactive .src-dot {{ background: {COLORS["muted_dim"]}; }}
.erd-sb-source .src-label {{ font-weight: 600; }}
.erd-sb-source .src-role {{
    color: {COLORS["muted"]};
    font-size: 0.72rem;
    margin-left: auto;
}}

/* ---------------------- Tabs (primary navigation) ---------------------- */
/* Turn the minimalist underlined tabs into clearly-clickable buttons. */
[data-testid="stTabs"] > div:first-child {{
    background: {COLORS["surface_alt"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 12px;
    padding: 6px;
    gap: 4px;
    margin-bottom: 1rem;
}}

/* The tablist strip — remove the native underline bar. */
[data-testid="stTabs"] [role="tablist"] {{
    border-bottom: none !important;
    gap: 4px;
}}

/* Individual tab buttons — generous padding, bigger type, subtle surface. */
[data-testid="stTabs"] [role="tab"] {{
    padding: 12px 20px !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.01em;
    color: {COLORS["muted"]} !important;
    border-radius: 8px !important;
    border: 1px solid transparent !important;
    transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
}}

[data-testid="stTabs"] [role="tab"]:hover {{
    background: {COLORS["surface"]};
    color: {COLORS["text"]} !important;
    border-color: {COLORS["border"]} !important;
}}

[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
    background: {COLORS["surface"]};
    color: {COLORS["accent"]} !important;
    border-color: {COLORS["accent"]} !important;
    box-shadow: 0 0 0 1px {COLORS["accent"]}22;
}}

/* Hide Streamlit's built-in underline indicator — our background+border does the job. */
[data-testid="stTabs"] [role="tablist"] > div[data-baseweb="tab-border"],
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {{
    display: none !important;
}}

/* ---------------------- DataFrame ---------------------- */
[data-testid="stDataFrame"] {{
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    overflow: hidden;
}}

/* ---------------------- Dividers ---------------------- */
[data-testid="stDivider"] {{
    border-color: {COLORS["border"]};
    margin: 1rem 0;
}}

/* ---------------------- Buttons ---------------------- */
.stButton > button {{
    border-radius: 8px;
    font-weight: 500;
    border: 1px solid {COLORS["border"]};
    transition: border-color 0.15s ease, background 0.15s ease;
}}
.stButton > button:hover {{
    border-color: {COLORS["accent"]};
}}

/* ---------------------- Radio (timeframe toggle) ---------------------- */
[data-testid="stRadio"] label {{
    font-weight: 500;
    font-size: 0.875rem;
}}

/* ---------------------- Info / warning / error boxes ---------------------- */
[data-testid="stAlert"] {{
    border-radius: 8px;
    border: 1px solid {COLORS["border"]};
}}

/* ---------------------- Containers with border — give them depth ---------------------- */
[data-testid="stVerticalBlockBorderWrapper"] {{
    border-radius: 10px !important;
    background: linear-gradient(180deg, {COLORS["surface"]} 0%, {COLORS["surface_alt"]} 100%);
}}

/* ---------------------- Hide Streamlit branding ---------------------- */
#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}
</style>
"""


def apply_theme() -> None:
    """Inject the custom theme CSS. Call once from `app.py` at startup."""
    st.markdown(_CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: Optional[str] = None) -> None:
    """Consistent page-level heading for every tab.

    Renders a title with an accent underline rule and an optional subtitle.
    Replaces the inconsistent mix of `st.header` + `st.caption` across views.
    """
    sub = f'<div class="erd-subtitle">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f'<div class="erd-page-header"><h1>{title}</h1>{sub}</div>',
        unsafe_allow_html=True,
    )


# Valid tone keywords — see CSS `.erd-tone-*` classes. Keep in sync with
# the per-tone CSS block in _CSS above.
_VALID_TONES = {"accent", "gain", "loss", "warn", "cool", "purple", "muted"}


def section_label(text: str, icon: Optional[str] = None, tone: str = "accent") -> None:
    """Small-caps section label — use for sub-sections inside a tab.

    Args:
        text: The label text (will be rendered uppercase).
        icon: Optional short string — usually a single emoji — rendered in
            a small bordered chip to the left of the text.
        tone: Color keyword for the left accent tick, icon-chip tint, and
            heading text. One of: accent, gain, loss, warn, cool, purple, muted.

    Slots between `st.subheader` and the metric-card grid. Replaces ad-hoc
    `st.markdown("**Valuation**")` usages and gives each section a role-based
    visual accent — adopted from the AI Brief's per-section treatment.
    """
    if tone not in _VALID_TONES:
        tone = "accent"
    icon_html = (
        f'<span class="erd-section-icon">{icon}</span>' if icon else ""
    )
    st.markdown(
        f'<div class="erd-section-label erd-tone-{tone}">'
        f'{icon_html}<span class="erd-section-text">{text}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def callout(
    body: str,
    *,
    tone: str = "accent",
    icon: Optional[str] = None,
    heading: Optional[str] = None,
) -> None:
    """Hero-style highlighted block — for standout moments.

    Used for the "Biggest mover today" surface and similar punch-line
    statements that shouldn't look like a generic `st.info`. Body accepts
    inline HTML/markdown (bold, links). Style mirrors the AI Brief's
    per-section cards — accent-tinted gradient, icon chip, tone border.

    Args:
        body: HTML-safe body text. Supports `<strong>`, `<em>`, `<a>`.
        tone: accent / gain / loss / warn / cool / purple / muted.
        icon: Optional short glyph rendered in a tone-tinted chip.
        heading: Optional small-caps label above the body.
    """
    if tone not in _VALID_TONES:
        tone = "accent"
    icon_html = (
        f'<div class="erd-callout-icon">{icon}</div>' if icon else ""
    )
    heading_html = (
        f'<div class="erd-callout-heading">{heading}</div>' if heading else ""
    )
    st.markdown(
        f'<div class="erd-callout erd-tone-{tone}">'
        f'{icon_html}'
        f'<div class="erd-callout-text">'
        f'{heading_html}'
        f'<div class="erd-callout-body">{body}</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
