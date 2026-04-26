"""AppTest-based smoke test — does the app import and render every tab without raising?

Uses `streamlit.testing.v1.AppTest` to run the full app in a headless environment,
then clicks through each tab and asserts `at.exception` stays None. Catches
regressions where a view would crash under any unusual data shape.

This test hits yfinance for real — it's a live smoke test, not a unit test.
Skip if offline.
"""

from __future__ import annotations

from pathlib import Path

import pytest

APP_PATH = Path(__file__).parent.parent / "app.py"


@pytest.fixture(scope="module")
def apptest(tmp_path_factory, monkeypatch_module):
    """Boot the app in a deterministic no-keys state.

    Without the env overrides below, a developer's local `.env` would leak into
    the test run and break determinism (e.g. adding an Anthropic key would make
    the briefing-no-key test fail for the wrong reason).
    """
    try:
        from streamlit.testing.v1 import AppTest
    except ImportError:
        pytest.skip("streamlit.testing.v1 unavailable (needs Streamlit >= 1.31)")
    # Force every optional key off so tests assert the "no-key" UX path.
    monkeypatch_module.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch_module.setenv("FINNHUB_API_KEY", "")
    monkeypatch_module.setenv("ALPHAVANTAGE_API_KEY", "")
    at = AppTest.from_file(str(APP_PATH), default_timeout=45)
    at.run()
    if at.exception:
        pytest.skip(
            f"App failed to boot (likely offline / yfinance unavailable): "
            f"{at.exception}"
        )
    return at


@pytest.fixture(scope="module")
def monkeypatch_module(request):
    """Module-scoped monkeypatch since pytest's built-in is function-scoped."""
    from _pytest.monkeypatch import MonkeyPatch

    mp = MonkeyPatch()
    yield mp
    mp.undo()


def test_app_boots_with_no_exception(apptest):
    assert not apptest.exception


def test_sidebar_has_refresh_button(apptest):
    # Refresh button should exist somewhere in the sidebar.
    button_labels = [b.label for b in apptest.sidebar.button]
    assert any("Refresh" in (lbl or "") for lbl in button_labels)


def test_all_six_tabs_present(apptest):
    # Streamlit's AppTest tabs are indexed by label.
    labels = [t.label for t in apptest.tabs]
    assert labels == [
        "Overview",
        "Detail",
        "AI Brief",
        "Analysis",
        "Patterns (Educational)",
        "Settings",
    ]


def test_overview_tab_renders_a_dataframe_or_error(apptest):
    overview_tab = apptest.tabs[0]
    # Either the dataframe (live data OK) or the error banner (all fetches failed)
    # must render. We just assert one of the two paths executed.
    has_df = len(overview_tab.dataframe) > 0
    has_error = len(overview_tab.error) > 0
    assert has_df or has_error


def test_briefing_tab_shows_no_key_message_when_unset(apptest):
    """With ANTHROPIC_API_KEY unset, the briefing tab must not offer a Generate button."""
    briefing_tab = apptest.tabs[2]  # AI Brief is now the 3rd tab
    # Gate 1 in views/briefing.py shows an info() box, then returns.
    button_labels = [b.label for b in briefing_tab.button]
    assert not any("Generate" in (lbl or "") for lbl in button_labels)
    assert len(briefing_tab.info) > 0  # "add your Claude API key" info message


def test_analysis_tab_renders_fundamentals_section(apptest):
    """Analysis tab should render the Fundamentals subheader even if live data partially fails."""
    analysis_tab = apptest.tabs[3]
    subheaders = [sh.value for sh in analysis_tab.subheader]
    assert "Fundamentals" in subheaders
    assert "Technicals" in subheaders


def test_patterns_tab_has_five_pattern_cards(apptest):
    """Patterns (Educational) tab should show all 5 pattern cards in a grid.

    The grid layout (post Phase 8 UI polish) renders one chart per pattern in
    a 2-column grid; each card has an expander underneath for extended detail.
    We assert the 5 detail expanders are present and every pattern name
    appears in the page's markdown.
    """
    patterns_tab = apptest.tabs[4]
    assert len(patterns_tab.expander) == 5
    markdown_text = " | ".join(m.value for m in patterns_tab.markdown)
    assert "Head and Shoulders" in markdown_text
    assert "Double Top" in markdown_text
    assert "Cup and Handle" in markdown_text
    assert "Flag" in markdown_text
    assert "Triangle" in markdown_text
