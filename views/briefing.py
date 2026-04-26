"""AI Briefing tab — Claude Sonnet 4.6 weekly briefing with §5.6 safeguards.

Reminder — this is the ONLY place `lib/briefing_engine.generate_briefing`
is invoked. Do not import it elsewhere.

The ten §5.6 non-negotiable safeguards, mapped to code here:

1. Budget cap env var: `settings.anthropic_monthly_budget_usd` from .env.
2. Pre-call cost disclosure: the Generate button label shows `~$0.05`.
3. Confirmation dialog every call: `_confirm_dialog` is an `st.dialog`.
4. Rate limit: `BudgetStatus.is_rate_limited` disables the button.
5. Hard monthly cap: `BudgetStatus.is_capped` disables the button entirely.
6. No background calls: `generate_briefing` is called only inside the
   dialog's Confirm-button branch, never at module load or on rerun.
7. Per-call usage ledger: every successful call appends to
   `briefings/.usage.jsonl` via `append_usage`.
8. Graceful 429 handling: `BriefingRateLimited` caught, user told to wait.
9. Same-day output cache: `briefings/YYYY-MM-DD.md`; "Force regenerate"
   button re-runs the cost disclosure.
10. Startup budget reminder: implemented in `setup_check.py`.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import streamlit as st

from config.settings import Settings, project_root
from config.theme import page_header
from data_sources.orchestrator import DataOrchestrator
from lib.briefing_engine import (
    BriefingAPIError,
    BriefingError,
    BriefingNoKey,
    BriefingRateLimited,
    build_watchlist_context,
    generate_briefing,
    load_prompt_template,
    render_user_prompt,
    strip_frontmatter,
)
from lib.briefing_render import render_briefing
from lib.budget import (
    ESTIMATED_COST_PER_BRIEFING,
    MODEL_ID,
    UsageEntry,
    append_usage,
    compute_status,
)
from lib.formatting import escape_streamlit_dollars

log = logging.getLogger(__name__)

BRIEFINGS_DIR = project_root() / "briefings"
USAGE_LOG = BRIEFINGS_DIR / ".usage.jsonl"
PROMPT_TEMPLATE = project_root() / "config" / "briefing_prompt.md"


def _today_cache_path() -> Path:
    return BRIEFINGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.md"


def _load_cached_briefing() -> str | None:
    p = _today_cache_path()
    if p.exists():
        try:
            return p.read_text(encoding="utf-8")
        except OSError:
            return None
    return None


def _write_cached_briefing(markdown: str) -> None:
    BRIEFINGS_DIR.mkdir(parents=True, exist_ok=True)
    _today_cache_path().write_text(markdown, encoding="utf-8")


def _render_budget_meter(status) -> None:
    col1, col2 = st.columns([3, 2])
    with col1:
        st.progress(
            status.pct_used,
            text=f"Anthropic spend this month: ${status.month_spend:.2f} / ${status.month_cap:.2f}",
        )
    with col2:
        if status.minutes_since_last is not None:
            mins_ago = int(status.minutes_since_last)
            if mins_ago < 60:
                when = f"{mins_ago} min ago"
            elif mins_ago < 60 * 24:
                when = f"{mins_ago // 60} hr ago"
            else:
                when = f"{mins_ago // (60 * 24)} day(s) ago"
            st.caption(f"Last briefing: {when}")
        else:
            st.caption("No briefings yet this session.")

    # Proactive warning at 80% — don't wait for the hard cap to surprise her.
    if 0.80 <= status.pct_used < 1.0:
        remaining = status.month_cap - status.month_spend
        st.warning(
            f"Approaching monthly cap: **${status.month_spend:.2f}** spent, "
            f"**${remaining:.2f}** remaining until the button disables. "
            f"Resets on {status.next_month_start.strftime('%B %d')}."
        )


def _generate_and_persist(settings: Settings, orch: DataOrchestrator) -> tuple[str | None, str | None, str | None]:
    """Run one briefing end-to-end. Returns (markdown, error, warning).

    - `error`: the call failed entirely; `markdown` is None.
    - `warning`: the call succeeded and `markdown` is present, but a
      non-critical side-effect failed (e.g. could not write the cache file).
      User gets the briefing; agent gets an advisory message.

    This is the single call site for `generate_briefing`. Invoked only
    from the dialog's Confirm button branch below.
    """
    try:
        system_prompt, user_template = load_prompt_template(PROMPT_TEMPLATE)
    except (BriefingError, OSError) as e:
        return None, f"Prompt template error: {e}", None

    context = build_watchlist_context(settings, orch)
    user_prompt = render_user_prompt(user_template, context)

    try:
        result = generate_briefing(
            api_key=settings.anthropic_key,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
    except BriefingNoKey:
        return None, "ANTHROPIC_API_KEY is not set. Ask your agent to add it.", None
    except BriefingRateLimited:
        return (
            None,
            "Anthropic rate-limited the request (HTTP 429). Try again later — "
            "the app will NOT retry automatically.",
            None,
        )
    except BriefingAPIError as e:
        return None, f"Anthropic call failed: {e}", None

    # Anthropic has already been charged at this point. Any disk failure
    # below is non-fatal for display but MUST be surfaced clearly so the user
    # knows to record the spend manually.
    warnings: list[str] = []

    # Persist — ledger FIRST (per §5.6 #7), then cache the output (markdown
    # with YAML provenance frontmatter prepended).
    try:
        append_usage(
            USAGE_LOG,
            UsageEntry(
                timestamp=datetime.now(),
                model=result.model,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                cost_usd=result.cost_usd,
            ),
        )
    except OSError as e:
        log.exception("Failed to append to usage ledger")
        warnings.append(
            f"⚠ Charged **${result.cost_usd:.4f}** by Anthropic but could NOT "
            f"write the usage ledger ({e}). The monthly-spend counter will be "
            f"inaccurate. Check file permissions on `briefings/.usage.jsonl` "
            f"and record this cost manually."
        )

    try:
        watchlist_symbols = [t.symbol for t in settings.tickers]
        _write_cached_briefing(result.with_frontmatter(watchlist_symbols))
    except OSError as e:
        log.exception("Failed to write briefing cache")
        warnings.append(
            f"Could not save the briefing to disk ({e}). The briefing is "
            f"displayed below — copy it now; it won't be cached for later."
        )

    warning = "\n\n".join(warnings) if warnings else None
    return result.markdown, None, warning


def _run_confirm_dialog(
    settings: Settings,
    orch: DataOrchestrator,
    status,
    force_regenerate: bool,
) -> None:
    """Open the confirmation dialog. Confirm branch is the SOLE call site."""

    next_month_str = status.next_month_start.strftime("%B %d")

    @st.dialog("Confirm AI briefing")
    def _dialog():
        st.write(
            f"This will use approximately **${ESTIMATED_COST_PER_BRIEFING:.2f}** of "
            f"your Anthropic API budget."
        )
        st.write(
            f"You've used **${status.month_spend:.2f}** of **${status.month_cap:.2f}** "
            f"this month. Budget resets on {next_month_str}."
        )
        if force_regenerate:
            st.caption(
                "Note: today's briefing is cached. Confirming will overwrite it "
                "with a fresh one."
            )
        st.divider()
        c1, c2 = st.columns(2)
        if c1.button("Cancel", use_container_width=True):
            st.rerun()
        if c2.button("Confirm & generate", type="primary", use_container_width=True):
            with st.spinner("Generating briefing..."):
                markdown, err, warn = _generate_and_persist(settings, orch)
            if err:
                st.session_state["briefing_error"] = err
            else:
                st.session_state["briefing_success"] = True
                if warn:
                    st.session_state["briefing_warning"] = warn
            st.rerun()

    _dialog()


def render(settings: Settings, orch: DataOrchestrator) -> None:
    page_header(
        "AI Brief",
        "Daily watchlist briefing generated by Claude Sonnet 4.6. Cached locally; "
        "regeneration is gated by cost, confirmation, and a monthly budget cap.",
    )

    # --- Gate 1: key required ---
    if not settings.has_anthropic:
        st.info(
            "AI briefings require an Anthropic API key. Say to your agent: "
            "*\"Help me add my Claude API key so I can get AI briefings.\"* "
            "Default monthly budget is **$5.00** — adjustable in `.env`."
        )
        st.caption(f"Model: `{MODEL_ID}` · Estimated cost per briefing: ~${ESTIMATED_COST_PER_BRIEFING:.2f}")
        return

    # --- Compute status (spend / rate limit / caps) ---
    status = compute_status(
        log_path=USAGE_LOG,
        monthly_cap_usd=settings.anthropic_monthly_budget_usd,
        min_minutes_between=settings.anthropic_min_minutes_between_briefings,
    )

    _render_budget_meter(status)

    # --- Show any result / error / warning from a prior dialog confirmation ---
    err = st.session_state.pop("briefing_error", None)
    if err:
        st.error(err)
    if st.session_state.pop("briefing_success", None):
        st.success("New briefing generated.")
    warn = st.session_state.pop("briefing_warning", None)
    if warn:
        st.warning(warn)

    st.divider()

    cached = _load_cached_briefing()
    if cached:
        today_str = datetime.now().strftime("%Y-%m-%d")
        col_cap, col_dl = st.columns([3, 1])
        with col_cap:
            st.caption(
                f"Cached from earlier today ({today_str}). "
                "Use Force regenerate to create a fresh one."
            )
        with col_dl:
            st.download_button(
                label="⬇ Download .md",
                data=cached.encode("utf-8"),
                file_name=f"briefing-{today_str}.md",
                mime="text/markdown",
                use_container_width=True,
                help="Full markdown with YAML provenance frontmatter",
            )
        # Render each section as its own styled card. The briefing renderer
        # classifies headings (TL;DR / Snapshot / Themes / Risk / Earnings /
        # Questions) and applies a per-section visual treatment. Dollar-sign
        # escaping happens inside the renderer (via HTML entity `&#36;`) so
        # Streamlit's KaTeX doesn't math-render prices.
        body = strip_frontmatter(cached)
        html = render_briefing(body)
        if html:
            st.markdown(html, unsafe_allow_html=True)
        else:
            # Fallback — if the briefing has no `### ` headings, render flat.
            st.markdown(escape_streamlit_dollars(body))

    # --- Gate 2: hard monthly cap ---
    if status.is_capped:
        next_date = status.next_month_start.strftime("%B %d, %Y")
        st.error(
            f"**Monthly Anthropic budget reached** (${status.month_spend:.2f} / "
            f"${status.month_cap:.2f}). The button re-enables on **{next_date}** "
            f"or when you raise `ANTHROPIC_MONTHLY_BUDGET_USD` in `.env`. "
            f"Ask your agent: *\"Raise my Anthropic monthly budget.\"*"
        )
        return

    # --- Gate 3: rate limit ---
    if status.is_rate_limited:
        mins = int(status.minutes_until_allowed or 0)
        st.warning(
            f"You generated a briefing **{int(status.minutes_since_last or 0)} min ago**. "
            f"Wait ~{mins} min for the next one, or adjust "
            f"`ANTHROPIC_MIN_MINUTES_BETWEEN_BRIEFINGS` in `.env`."
        )
        return

    # --- Generate button(s) ---
    label = (
        f"🔁 Force regenerate (~${ESTIMATED_COST_PER_BRIEFING:.2f})"
        if cached
        else f"📝 Generate Briefing (~${ESTIMATED_COST_PER_BRIEFING:.2f})"
    )
    if st.button(label, type="primary"):
        _run_confirm_dialog(settings, orch, status, force_regenerate=bool(cached))

    st.caption(
        f"Model: `{MODEL_ID}` · All Anthropic calls require explicit confirmation · "
        f"Usage ledger: `briefings/.usage.jsonl` (gitignored)"
    )
