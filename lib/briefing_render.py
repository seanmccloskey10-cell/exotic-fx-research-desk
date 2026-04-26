"""Briefing renderer — parses the Claude-generated markdown into sections and
produces custom-styled HTML cards per section.

The briefing follows a fixed structure (see `config/briefing_prompt.md`):
TL;DR → Watchlist snapshot → Themes this week → Risk watch →
Earnings calendar → Questions to sit with.

Each section gets its own role-based visual treatment — headline hero for
TL;DR, amber warning tint for Risk watch, muted italic for Questions, a
table card for Earnings, etc. Rendering all six identically wastes the
daily-ritual surface.

HTML is produced via the `markdown` library (tables extension enabled).
Dollar signs are converted to the HTML entity `&#36;` after conversion so
Streamlit's KaTeX plugin doesn't math-render prices as italic serif.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Tuple

import markdown as md_lib


@dataclass(frozen=True)
class SectionStyle:
    """Visual config for one briefing section type."""
    kind: str           # CSS suffix: erd-bf-{kind}
    icon: str           # one-char or emoji glyph
    match_terms: Tuple[str, ...]  # lowercased substrings to classify this section


SECTION_STYLES: Tuple[SectionStyle, ...] = (
    # Order matters — `risk` must match before `snapshot` since "watchlist risk"
    # is possible but uncommon. Current order is defensive-first.
    SectionStyle("tldr", "📌", ("tl;dr", "tldr", "bottom line", "headline")),
    SectionStyle("snapshot", "📊", ("watchlist snapshot", "snapshot", "state of play")),
    SectionStyle("themes", "🧭", ("theme",)),
    SectionStyle("risk", "⚠️", ("risk", "watch-out", "caution")),
    SectionStyle("earnings", "📅", ("earnings calendar", "earnings", "calendar")),
    SectionStyle("questions", "💭", ("question", "to sit with", "journal", "reflection")),
)

DEFAULT_STYLE = SectionStyle("generic", "•", ())


def classify_heading(heading: str) -> SectionStyle:
    """Pick the right visual style for this heading's content."""
    lower = heading.lower().strip()
    for style in SECTION_STYLES:
        if any(term in lower for term in style.match_terms):
            return style
    return DEFAULT_STYLE


def split_sections(body: str) -> List[Tuple[str, str]]:
    """Split a briefing body into (heading, content) pairs.

    Splits on any level-3 heading (`### Title`). Content before the first
    `###` is discarded — per the prompt, the briefing never starts with
    preamble, but if the model slips one in it's noise, not signal.
    """
    if not body:
        return []
    # `re.split` with a capturing group returns the delimiters interleaved.
    parts = re.split(r"(?m)^###[ \t]+(.+?)\s*$", body)
    if len(parts) < 3:
        # No ### headings found — render the whole body as one generic section.
        return [("Briefing", body.strip())]
    sections: List[Tuple[str, str]] = []
    # parts[0] is pre-first-heading content (usually empty); skip.
    for i in range(1, len(parts), 2):
        heading = parts[i].strip()
        content = parts[i + 1].strip() if i + 1 < len(parts) else ""
        if heading or content:
            sections.append((heading, content))
    return sections


def _body_to_html(markdown_body: str, style: SectionStyle) -> str:
    """Convert a section's markdown body to HTML.

    For the `questions` section we additionally wrap the body in a
    blockquote-ish container via a dedicated CSS class.
    """
    html = md_lib.markdown(
        markdown_body,
        extensions=["tables", "sane_lists"],
        output_format="html",
    )
    # Replace `$` with its HTML entity — Streamlit's KaTeX math plugin sees
    # any literal `$` in a text node and pairs it with the next one.
    html = html.replace("$", "&#36;")
    return html


def render_section(heading: str, body: str) -> str:
    """Build one HTML card for a heading + body pair."""
    style = classify_heading(heading)
    body_html = _body_to_html(body, style)
    return (
        f'<section class="erd-bf-section erd-bf-{style.kind}">'
        f'<div class="erd-bf-title">'
        f'<span class="erd-bf-icon" aria-hidden="true">{style.icon}</span>'
        f'<span class="erd-bf-heading">{heading}</span>'
        f'</div>'
        f'<div class="erd-bf-body">{body_html}</div>'
        f'</section>'
    )


def render_briefing(body_markdown: str) -> str:
    """Top-level entry point. Returns a single HTML string to pass to
    `st.markdown(..., unsafe_allow_html=True)`.

    The body should be the briefing with YAML frontmatter already stripped.
    """
    sections = split_sections(body_markdown)
    if not sections:
        return ""
    cards = "".join(render_section(h, b) for h, b in sections)
    return f'<div class="erd-bf-root">{cards}</div>'
