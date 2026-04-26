"""Tests for lib/briefing_render — section classification + splitting + HTML shape.

The CSS is not tested here; it's cosmetic. What would silently regress is the
section classifier (TL;DR headings must map to the `tldr` style so the hero
card renders correctly) and the splitter (a missed heading would collapse
sections into each other).
"""

from __future__ import annotations

from lib.briefing_render import (
    DEFAULT_STYLE,
    classify_heading,
    render_briefing,
    render_section,
    split_sections,
)


# ---------- classify_heading ----------

def test_classify_tldr_variants():
    for h in ("TL;DR", "tl;dr", "Tldr", "TLDR"):
        assert classify_heading(h).kind == "tldr"


def test_classify_snapshot():
    assert classify_heading("Watchlist snapshot").kind == "snapshot"
    assert classify_heading("Snapshot").kind == "snapshot"


def test_classify_themes():
    assert classify_heading("Themes this week").kind == "themes"


def test_classify_risk():
    assert classify_heading("Risk watch").kind == "risk"


def test_classify_earnings():
    assert classify_heading("Earnings calendar").kind == "earnings"


def test_classify_questions():
    assert classify_heading("Questions to sit with").kind == "questions"


def test_classify_unknown_heading_returns_default():
    assert classify_heading("Some random custom heading").kind == DEFAULT_STYLE.kind


# ---------- split_sections ----------

def test_split_sections_basic():
    body = (
        "### TL;DR\nLead headline here.\n\n"
        "### Watchlist snapshot\nOne paragraph.\n\n"
        "### Risk watch\nAmber alerts.\n"
    )
    sections = split_sections(body)
    assert len(sections) == 3
    assert sections[0][0] == "TL;DR"
    assert sections[0][1] == "Lead headline here."
    assert sections[1][0] == "Watchlist snapshot"
    assert sections[2][0] == "Risk watch"


def test_split_sections_empty_body_returns_empty():
    assert split_sections("") == []


def test_split_sections_no_headings_returns_one_generic_section():
    body = "Just some flat text, no headings."
    sections = split_sections(body)
    assert len(sections) == 1
    assert sections[0][0] == "Briefing"
    assert "flat text" in sections[0][1]


def test_split_sections_preamble_before_first_heading_is_discarded():
    body = "Pre-heading noise.\n\n### TL;DR\nThe real content.\n"
    sections = split_sections(body)
    assert len(sections) == 1
    assert sections[0][0] == "TL;DR"
    assert "noise" not in sections[0][1]


# ---------- render_section ----------

def test_render_section_produces_classed_html():
    html = render_section("TL;DR", "Short headline.")
    assert 'class="erd-bf-section erd-bf-tldr"' in html
    assert "Short headline" in html
    assert 'class="erd-bf-heading"' in html


def test_render_section_escapes_dollars_as_html_entity():
    # KaTeX would otherwise math-italicize the $189.49 / $IREN pairs.
    html = render_section("Watchlist snapshot", "$IREN at $189.49 led.")
    assert "$" not in html  # every literal $ converted to &#36;
    assert "&#36;IREN" in html
    assert "&#36;189.49" in html


def test_render_section_renders_markdown_bold():
    html = render_section("Risk watch", "**CRDO** looks stretched.")
    assert "<strong>CRDO</strong>" in html


def test_render_section_renders_tables():
    md = "| Date | Ticker |\n|---|---|\n| 2026-05-01 | CRDO |"
    html = render_section("Earnings calendar", md)
    assert "<table>" in html
    assert "<th>Date</th>" in html
    assert "<td>CRDO</td>" in html


# ---------- render_briefing (end-to-end) ----------

def test_render_briefing_wraps_in_root():
    body = "### TL;DR\nHeadline.\n\n### Risk watch\nAmber.\n"
    out = render_briefing(body)
    assert 'class="erd-bf-root"' in out
    assert out.count("erd-bf-section") == 2


def test_render_briefing_empty_returns_empty():
    assert render_briefing("") == ""
