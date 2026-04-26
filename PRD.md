# FX Research Desk — PRD

**Status:** Initial scaffold shipped 2026-04-26
**Repo type:** Public, generic teaching template — usable by any FX research professional who wants a local-first, agent-operated dashboard. Forked from a prior `equity-research-desk` template; see git history for the parent shape.

---

## 1. Overview

A local-first, browser-native FX research dashboard built in Python + Streamlit + Plotly. Clones from GitHub, runs with one command, displays a multi-tab dashboard for a configurable FX watchlist (default seed: G10 + EM + exotic pairs via yfinance). Operated via natural-language prompts to the user's AI coding agent (Claude Code in VS Code). Designed to work with **zero API keys** out of the box (yfinance) and gracefully unlock additional features when the user adds Finnhub, Alpha Vantage, or Anthropic API keys.

This repo is also a **canonical template for similar domain-specific tools.** The architecture is forkable into any per-instrument research surface (equities, FX, commodities, crypto if you want it). The shape stays the same; only the data layer + briefing register + watchlist defaults change.

---

## 2. Target user

An FX research professional — comfortable with Claude (e.g. Cowork user), but **not a developer**. The user does not type commands directly; they tell their Claude Code agent what they want in natural language and the agent does the work.

The user is assumed to have:
- A live market data source already (Bloomberg, Refinitiv, broker terminal, etc.) — this tool is the *synthesis layer over* their existing data, not a replacement for it
- Some interest in or watchlist across G10, EM, or exotic FX pairs — the default seed is generic but easy to swap
- A Claude plan and Claude Code installed (per the README's bootstrap section)

The user does NOT need to be code-fluent. The tool's design assumption: every install, configuration, and extension happens by talking to the agent in plain English.

---

## 3. Core UX principle — agent-operated, not human-operated

**The user never types a command directly.** Every action — cloning, installing, running, extending — happens because they tell their Claude Code agent in plain English what they want.

This shapes the whole project:

- The README is written for the user to paste to their agent (or for the agent to parse), not for the user to execute step-by-step
- `PROMPTS.md` is a cookbook of example sentences the user can say to extend the tool
- `CLAUDE.md` at the project root teaches whatever agent runs in the project how the code is organized, how to extend it, and what conventions to follow
- Error messages are written so the agent can read them and diagnose
- Every feature has an associated "what to say to your agent" example

**Mental model for any builder agent:** treat the user's Claude Code as a co-pilot who's now on the team. The tool's code should be clean enough to read, the docs structured enough to teach the agent, and the architecture modular enough that the agent can extend it without rewriting anything.

---

## 4. Success criteria

The build is successful if and only if:

1. **Zero-key start.** A user can clone the repo and, with zero API keys configured, have a working dashboard displaying live FX data within ~5 minutes of saying "set this up for me" to their agent.
2. **Visible sophistication.** On first load, the dashboard *looks like* a paid product — dark theme, interactive candlestick charts, color-coded metrics, clean typography.
3. **Redundancy.** If Finnhub, Alpha Vantage, or Anthropic API keys are missing or broken, the tool continues to work with graceful fallback to yfinance.
4. **Extensibility.** A user can say "add USDPLN to my watchlist" or "add a CB calendar view" to their agent and the agent can do it by following documented patterns in `CLAUDE.md` — without rewriting core code.
5. **No OS gotchas.** Setup and error handling account for macOS-specific traps (TextEdit rich-text default, Finder extension-hiding, `python3` vs `python`) and document Windows alternatives (`.env.txt` hidden-extension trap, `python` vs `py`, PowerShell vs bash, `winget` installs).
6. **One-command run.** After first setup, `python3 run.py start` (executed by the agent, not the user) is the only command needed to launch.

---

## 5. Functional requirements

### 5.1 Views (tabs in Streamlit)

1. **Overview** — watchlist table, all pairs at a glance, sparklines, sortable
2. **Per-pair detail** — header with price + day change, metric cards (52W High, 52W Low, technicals), Plotly candlestick chart with timeframe toggles (1D / 5D / 1M / 3M / 6M / 1Y / 5Y), recent news panel (last 10 articles when Finnhub key is set), description
3. **AI Brief** — "Generate weekly briefing" button; if `ANTHROPIC_API_KEY` is set, calls Claude API with structured context across the watchlist; output is a markdown briefing covering themes, risks, and questions; cached to `briefings/YYYY-MM-DD.md`; falls back to a "set up an Anthropic key to unlock" message if no key
4. **Analysis** — per-pair deep dive with technical indicators (RSI, MACD, SMAs)
5. **Patterns (Educational)** — reference library of chart patterns (head & shoulders, double top, etc.) for users who want a visual primer
6. **Settings** — READ-ONLY view of key status and copyable prompts (the user asks the agent to mutate `.env`, never the UI)

### 5.2 Sidebar (persistent across tabs)

- Title: "FX Research Desk"
- Watchlist — all pairs with current price and day-% color-coded
- Refresh button — clears cache, re-fetches
- Last-refreshed timestamp
- Data sources panel — shows which optional sources are active (Finnhub / Alpha Vantage / Anthropic)
- Market session indicator — currently NYSE-derived (informational; FX is 24/5)

### 5.3 Data sources (cascade priority)

1. **yfinance** (primary, no key) — quotes, history, basic info for FX pairs
2. **Finnhub** (optional, free tier) — news, additional fundamentals
3. **Alpha Vantage** (optional, free tier) — backup source if Finnhub rate-limits

If a higher-priority source returns null for a field, the next source is tried. Views never branch on which source produced a value.

### 5.4 AI Briefing

- Triggered by an explicit button click in the AI Brief tab — never automatic, never on `st.rerun()`, never on page load
- Two-step UI: cost-disclosed button → confirmation dialog → API call
- Output cached to `briefings/YYYY-MM-DD.md`
- Usage ledger at `briefings/.usage.jsonl` enforces a monthly hard cap (configurable via `ANTHROPIC_MONTHLY_BUDGET_USD` env var, default $10)
- All Anthropic calls live in `views/briefing.py` and `lib/briefing_engine.py` — no other module imports `anthropic`
- Briefing prompt is editable in `config/briefing_prompt.md`

### 5.5 Watchlist management

- Default seed in `config/tickers.yaml` — G10 + EM + exotic FX pairs
- Add/remove pairs by editing the YAML directly (or by asking the agent to do it)
- yfinance FX symbol convention: `<BASE><QUOTE>=X` (e.g. `EURUSD=X`, `USDTRY=X`, `GBPJPY=X`)

### 5.6 Budget protection (the ten safeguards on AI Briefing)

The AI Briefing flow is the only place this app spends real money. Ten structural safeguards live in `views/briefing.py` and `lib/budget.py`:

1. **Hard monthly cap** — `ANTHROPIC_MONTHLY_BUDGET_USD` (default $10)
2. **Settings tab is READ-ONLY** — the UI cannot raise the cap
3. **No background calls** — only fires from explicit button click
4. **Confirmation dialog before call** — `st.dialog` with cost disclosed
5. **Usage ledger writes BEFORE display** — pre-paid transparency
6. **Same-day cache** — repeated calls in one day return cached result
7. **Rate limit** — minimum minutes between calls (configurable)
8. **Cost-disclosed button** — shows estimated $/call before click
9. **Hard-cap gate** — button disabled when month-to-date hits cap
10. **Single import site** — `anthropic` is imported in exactly one module

Modify `views/briefing.py` only after re-reading this section.

---

## 6. OS support

- **macOS** — first-class. `python3`, Homebrew or `.pkg` installer, GUI password dialog preferred over Terminal sudo for non-technical users.
- **Windows** — first-class. `python` (or `py`), `winget` installs, UAC dialog for elevated permissions.
- **Linux** — works (it's just Python + Streamlit + yfinance) but no first-class bootstrap docs.

The `run.py` wrapper handles platform-specific differences for venv paths, process management (`taskkill` vs `kill`), and PID file handling. The agent should use `python3` on macOS/Linux and `python` on Windows (or `py` if Python Launcher is the install).

---

## 7. Non-functional requirements

- **Local-first.** No data leaves the user's machine except the optional outbound API calls (yfinance, Finnhub, Alpha Vantage, Anthropic).
- **No telemetry.** No analytics, no tracking, no phone-home.
- **`.env` never committed.** `.gitignore` excludes it.
- **No background jobs.** The app does not run cron, does not auto-refresh data, does not auto-generate briefings.
- **No buy/sell/hold language anywhere.** This is analysis, not advice.

---

## 8. Out of scope

- Trade execution (this is a research tool, not a broker)
- Position tracking (use a separate tool or your broker's interface)
- Real-time tick data (yfinance is delayed; that's fine for research)
- Mobile UI (Streamlit responsive on mobile but not optimized)
- Multi-user / multi-tenant (this is a personal tool, one user per install)
- Crypto (FX pairs only by default; you can add crypto pairs to `tickers.yaml` if you want, but the briefing prompt is FX-shaped)

---

## 9. How to extend

See `CLAUDE.md` → "Extension patterns" for:
- Adding a new pair (edit `tickers.yaml`, hit Refresh)
- Adding a new data source (subclass `DataSource`, register in orchestrator)
- Adding a new view / tab (create `views/<name>.py`, register in `app.py`)
- Adding a component (create `components/<name>.py`)
- Changing theme / styling (`config/theme.py`)
- Adding or rotating an API key (edit `.env`, restart dashboard)

---

## 10. Inherited from the equity-research-desk parent

This repo is a fork. Most of the architecture, the `run.py` flow, the Streamlit shape, the `lib/` helpers, the budget protection pattern, the cascade orchestrator, and the bootstrap discipline are inherited from the equity-research-desk template. The FX variant changes:

- Watchlist (stocks → FX pairs)
- Briefing prompt (equity register → macro/FX register)
- Audience copy (equity-investor framing → FX-research framing)
- yfinance fundamentals fields ignored (P/E, market cap, EPS, etc. are null for FX)

The `run.py` wrapper, the `views/` Streamlit modules, the `lib/` helpers, the `config/` loader, the data-source orchestrator, the budget protection — all of these are unchanged from the parent.

---

## 11. Versioning

- 0.1.x — initial FX scaffold
- 0.2.x — when the FX-specific market-hours indicator (London/NY/Tokyo) replaces the inherited NYSE indicator (currently a known cosmetic gap)
- 1.0.x — when the tool has been used through one full quarterly research cycle and proven stable
