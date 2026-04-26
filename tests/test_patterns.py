"""Patterns (Educational) view — smoke tests.

Each pattern figure is pure Plotly over synthesized data, so we can exercise
the figure-builders directly without Streamlit. Also verify the catalogue
shape so that future edits don't silently drop entries or fields.
"""

from __future__ import annotations

import plotly.graph_objects as go

from views.patterns import (
    _PATTERNS,
    _ascending_triangle_fig,
    _cup_and_handle_fig,
    _double_top_fig,
    _flag_fig,
    _head_and_shoulders_fig,
)


def test_five_patterns_are_catalogued():
    assert len(_PATTERNS) == 5


def test_every_pattern_entry_has_required_fields():
    required = {"name", "bias", "fig", "what", "means", "fails"}
    for pat in _PATTERNS:
        missing = required - set(pat.keys())
        assert not missing, f"{pat.get('name')} missing {missing}"
        # Text fields aren't empty placeholders
        for key in ("what", "means", "fails"):
            assert len(pat[key]) > 40, f"{pat['name']}.{key} looks like a stub"


def test_every_figure_renders():
    for fig_fn in (
        _head_and_shoulders_fig,
        _double_top_fig,
        _cup_and_handle_fig,
        _flag_fig,
        _ascending_triangle_fig,
    ):
        fig = fig_fn()
        assert isinstance(fig, go.Figure)
        # Each figure has at least a price trace
        assert len(fig.data) >= 1


def test_every_figure_has_at_least_one_annotation():
    # Annotations are what make the patterns educational — catch accidental removal
    for fig_fn in (
        _head_and_shoulders_fig,
        _double_top_fig,
        _cup_and_handle_fig,
        _flag_fig,
        _ascending_triangle_fig,
    ):
        fig = fig_fn()
        assert len(fig.layout.annotations) >= 1
