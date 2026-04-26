"""Tests for lib/formatting helpers — the ones with non-trivial logic.

Most formatters are thin f-string wrappers and don't need coverage. The
one that does is `escape_streamlit_dollars` — it guards a user-visible
rendering bug (Streamlit's KaTeX eating `$price$` pairs as math mode),
and it has edge cases around pre-escaped strings.
"""

from __future__ import annotations

from lib.formatting import escape_streamlit_dollars


def test_escape_single_dollar():
    assert escape_streamlit_dollars("$189.49") == r"\$189.49"


def test_escape_multiple_dollars():
    assert (
        escape_streamlit_dollars("\$ZAR (+7.1%) and \$TRY (+3.4%)")
        == r"\\$ZAR (+7.1%) and \\$TRY (+3.4%)"
    )


def test_escape_preserves_already_escaped():
    # An already-escaped `\$` should not be double-escaped.
    assert escape_streamlit_dollars(r"\$100") == r"\$100"


def test_escape_mixed_escaped_and_raw():
    assert escape_streamlit_dollars(r"\$100 and $200") == r"\$100 and \$200"


def test_escape_no_dollars_is_identity():
    assert escape_streamlit_dollars("hello world") == "hello world"


def test_escape_none_returns_empty():
    assert escape_streamlit_dollars(None) == ""


def test_escape_empty_is_empty():
    assert escape_streamlit_dollars("") == ""


def test_escape_real_briefing_snippet():
    # The kind of text that triggered the bug: ticker with $ prefix
    # immediately followed by prose, then another $-ticker.
    text = "A green session led by \$ZAR (+7.1%) while \$BRL (-2.5%) lagged."
    expected = r"A green session led by \\$ZAR (+7.1%) while \\$BRL (-2.5%) lagged."
    assert escape_streamlit_dollars(text) == expected
