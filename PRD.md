# FX Research Desk — PRD

> **⚠ This PRD is INHERITED VERBATIM from the parent `equity-research-desk` repo.** It documents how the codebase was originally designed and shipped for Roula. The FX variant (this repo) reuses the same architecture, the same `run.py` flow, the same Streamlit shape — only the watchlist, briefing register, and audience differ. **Do NOT rewrite this PRD wholesale.** When you ship NEW work for the FX variant, prepend a "FX Variant Deltas" section above with the specific differences (e.g. "tickers swapped to FX pairs", "briefing prompt rewritten for macro register", "Bura is AI-fluent — less hand-holding than Roula"). The original PRD body below is reference, not a current spec.
>
> **Key FX-variant deltas as of 2026-04-26:**
> - Watchlist swapped to G10 + EM + exotic FX pairs (see [config/tickers.yaml](config/tickers.yaml))
> - Briefing prompt rewritten in macro/FX register (see [config/briefing_prompt.md](config/briefing_prompt.md)) — drops equity-specific fields (P/E, market cap, EPS, etc.) which yfinance returns null for FX
> - Audience: Bura (senior FX prop-desk operator, AI-fluent) — less hand-holding than Roula needed
> - "Crypto avoidance" rule from Roula's version dropped (not relevant to Bura)
> - Market-hours indicator still NYSE-derived (cosmetic gap; FX is 24/5 — see SESSION-NOTES.md for the deferred fix)

---

# Equity Research Desk — PRD (inherited body, preserved for reference)

**Owner:** Sean McCloskey
**For:** Roula (Preply student) — first canonical student deployment
**Status:** Scope locked 2026-04-21, not yet built
**Target ship:** Within a few days — replaces a failed in-lesson build

---

## 1. Overview

A local-first, browser-native equity research dashboard built in Python + Streamlit + Plotly. Clones from GitHub, runs with one command, displays a sophisticated multi-tab dashboard for a pre-configured watchlist (initially: CRDO, HIMS, BABA, QQQI, IREN). Operated via natural-language prompts to the student's AI coding agent (Claude Code in VS Code). Designed to work with **zero API keys** out of the box (via yfinance) and gracefully upgrade when the student adds Finnhub, Alpha Vantage, or Claude API keys.

This is also the **canonical template** for future Preply students who want a similar domain-specific tool. Build it so it's forkable and easily reshaped for other verticals (e.g. sports analytics, real estate, crypto alternatives).

---

## 2. Target user: Roula

Senior business professional at General Electric, based in Dubai. **Not technically savvy.** She uses Claude Cowork daily for meeting briefs, PDFs, presentations — she is AI-fluent but not code-fluent. Equities is a personal hobby on the side, not her GE job; this tool is a weekend-tea-and-stocks companion, not a professional trading system.

She has had ~10 Preply lessons with Sean. The last one attempted to build an equity research setup in VS Code but failed on a `.env` / browser / Finnhub integration. This tool replaces that failed build.

**Critical constraints on her experience:**

- **She does not type commands.** She talks to her Claude Code agent in natural language.
- **She does not know what `pip install`, `git clone`, `cd`, or `.env` mean.** Her agent handles all of that.
- **She is on macOS.** All setup and error-handling guidance is written Mac-first (`python3`, `brew`, Homebrew-preferred install paths, TextEdit rich-text trap, Finder extension-hiding). Windows guidance is kept as a secondary aside where relevant (for Sean testing, or future Windows students).
- **She has 5 tickers she cares about:** CRDO (Credo Technology), HIMS (Hims & Hers Health), BABA (Alibaba), QQQI (NEOS Nasdaq-100 Income ETF), IREN (Iris Energy).
- **She has a Claude API key available** (explicitly opted-in; Sean confirmed 2026-04-21). This unlocks the AI briefing feature.
- **She does not like crypto.** Equities only. Do not include crypto examples, crypto-adjacent features, or crypto tickers as demo data.

### Her learning style (from Sean's student notes)

- Learns by seeing **concrete results on screen** (a chart updates, a number appears, a page changes) — not abstract frameworks
- Previous lessons that were too abstract (e.g. "LLM Council") didn't land; demos that produce visible change ("a price appears") do
- She's a **Cowork-fluent power user** — she already trusts AI to do real work for her

---

## 3. Core UX principle — agent-operated, not human-operated

**The student never types a command.** Every action — cloning, installing, running, extending — happens because she tells her Claude Code agent in plain English what she wants.

This reshapes the whole project:

- The README is written for her to paste to her agent, not for her to execute
- `PROMPTS.md` is a cookbook of example sentences she can say
- `CLAUDE.md` at the project root teaches whatever agent runs in her project how the code is organized, how to extend it, and what conventions to follow
- Error messages are written so her agent can read them and diagnose
- Every feature has a "what to say to your agent" prompt associated with it

**Mental model for the builder agent:** treat the student's Claude Code as a co-pilot who's now on the team. The tool's code should be clean enough to read, the docs structured enough to teach the agent, and the architecture modular enough that the agent can extend it without rewriting anything.

---

## 4. Success criteria

The build is successful if and only if:

1. **Zero-key start.** Student can clone the repo and, with zero API keys configured, have a working dashboard displaying live data for her 5 tickers within 5 minutes of saying "set this up for me" to her agent.
2. **Visible sophistication.** On first load, the dashboard *looks like* a paid product — dark theme, interactive candlestick charts, color-coded metrics, clean typography. Not a student project.
3. **Redundancy.** If Finnhub, Alpha Vantage, or Claude API keys are missing or broken, the tool continues to work with graceful fallback to yfinance.
4. **Extensibility.** Student can say "add TSLA to my watchlist" or "add a sector breakdown view" to her agent and the agent can do it by following documented patterns in `CLAUDE.md` — without rewriting core code.
5. **No OS gotchas.** Setup and error handling account for macOS-specific traps (TextEdit rich-text default, Finder extension-hiding, `python3` vs `python`) and keep Windows gotchas documented as a secondary aside (`.env.txt` hidden-extension trap, `python` vs `py`, PowerShell vs bash).
6. **One-command run.** After first setup, `streamlit run app.py` (executed by the agent, not the student) is the only command needed to launch.

---

## 5. Functional requirements

### 5.1 Views (tabs in Streamlit)

1. **Overview** — watchlist table, all tickers at a glance, sparklines, sortable
2. **Per-ticker detail** — one tab per ticker (tab per ticker OR a dropdown selector): header with price + day change, metric cards (Market Cap, P/E, P/B, 52W High, 52W Low, Volume), Plotly candlestick chart with timeframe toggles (1D / 5D / 1M / 3M / 6M / 1Y / 5Y), recent news panel (last 10 articles), upcoming earnings date + estimate, company description
3. **Comparison** — all 5 tickers side-by-side: radar chart of normalized ratios (P/E, P/B, ROE, dividend yield, market cap), bar chart of YTD returns, table of key metrics
4. **AI Briefing** — "Generate weekly briefing" button; if `ANTHROPIC_API_KEY` is set, calls Claude API with structured context about the 5 stocks; output is a markdown briefing covering themes, risks, opportunities, earnings watch list; cached to `briefings/YYYY-MM-DD.md`; falls back to a "Set up AI briefings" message if no key
5. **Settings** — manage watchlist (add/remove tickers), configure API keys (with a text explaining what each key unlocks), theme toggle

### 5.2 Sidebar (persistent across tabs)

- Current watchlist with live prices + day % (color-coded)
- Refresh button (re-fetches data)
- Data source indicator (shows which sources are active — green dot for live, grey for not configured)

### 5.3 Sophistication touches (load-bearing for "looks premium")

- **Dark theme default** (Streamlit dark theme + custom CSS accent colors)
- **Color-coded gains/losses** — green for up, red for down, grey for flat
- **Candlestick charts** (not just line charts) with volume bars beneath
- **Sparkline mini-charts** inline in the watchlist table
- **Metric cards with delta indicators** (arrow up/down, color-coded)
- **Loading skeletons** while data is fetching — not just blank screens
- **Graceful error states** that tell the student's agent what's wrong and what to do (e.g. *"Finnhub news unavailable. If you want news, say to your agent: 'Help me add my Finnhub key to the .env file.'"*)

### 5.4 Data needed per ticker

From yfinance (primary, no key):
- Current price, day change %, day range, 52W range
- Market cap, P/E (trailing), P/B, dividend yield, ROE if available
- Volume + average volume
- Historical OHLC prices (for candlestick chart)
- Company name, sector, industry, short description

From Finnhub (optional enrichment):
- Recent news (last 10 articles with links)
- Upcoming earnings date + estimate
- Analyst recommendations (stretch)

From Alpha Vantage (optional enrichment, tertiary):
- Additional fundamentals if Finnhub is down or missing
- Currently no planned unique use — included as the third backup for robustness

### 5.5 AI Briefing content (when Claude API key is present)

Input to Claude: structured JSON payload with all 5 tickers' data from the dashboard (prices, key ratios, recent news headlines, upcoming earnings).

Output format (markdown):
- **Portfolio snapshot** (1 paragraph)
- **Themes this week** (2-3 bullet points linking tickers by shared narratives, e.g. semiconductors, Chinese tech, Bitcoin mining)
- **Risk watch** (what could go wrong, per ticker or thematic)
- **Earnings calendar** (upcoming earnings she should watch)
- **Questions to sit with** (3-4 open questions for her research journal)

**Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`) — locked. Do not use Opus (5× cost, not needed for this analysis).

**Cost envelope:** ~$0.05 per briefing. Weekly ritual: ~$0.20/month.

### 5.6 Anthropic API budget protection (non-negotiable)

Roula's Anthropic account must be protected from accidental overspend. Every one of the following must be implemented — not optional:

1. **Budget cap env var.** `ANTHROPIC_MONTHLY_BUDGET_USD` in `.env`, default `5.00` (five dollars per month). Tracked in `briefings/.usage.jsonl`.
2. **Pre-call cost disclosure.** The "Generate Briefing" button label shows the estimated cost inline — e.g. `Generate Briefing (~$0.05)`.
3. **Confirmation dialog every call.** When she clicks, a Streamlit `st.dialog` or equivalent shows: *"This will use approximately $0.05 of your Anthropic API budget. You've used $X.XX of $5.00 this month. Continue?"* with Confirm / Cancel.
4. **Rate limit.** Default max 1 briefing per hour. Stored in settings, adjustable. A second click within 60 minutes surfaces: *"You generated a briefing X minutes ago. If you need a fresh one sooner, adjust the rate limit in Settings."*
5. **Hard monthly cap.** When `ANTHROPIC_MONTHLY_BUDGET_USD` is reached, the button is disabled with: *"Monthly Anthropic budget reached. The button will re-enable on [1st of next month] or when you raise the cap in your .env file."* No retries, no override button. She has to change `.env` manually (her agent can help).
6. **No background calls, ever.** Claude API is only invoked from the explicit button click. Never on page load. Never on `st.rerun()`. Never on schedule. Never on navigation. This must be enforced by isolating the Claude call inside a Streamlit button callback that cannot be triggered by rerender.
7. **Per-call usage ledger.** Every call appends `{timestamp, model, input_tokens, output_tokens, cost_usd}` to `briefings/.usage.jsonl`. Used for monthly total computation. File is gitignored.
8. **Graceful rate-limit handling.** If Anthropic returns 429, do not retry. Surface a clear message and stop.
9. **Output caching.** Same-day briefings are cached to `briefings/YYYY-MM-DD.md`. Clicking regenerate on the same day returns the cached version with a "Cached from earlier today" banner and a "Force regenerate" button that re-runs cost disclosure.
10. **Startup budget reminder.** `setup_check.py` prints the current month's spend (e.g. *"Anthropic spend this month: $0.15 / $5.00"*) when the Anthropic key is configured.

Acceptance test: a malicious or buggy caller trying to call the Claude endpoint 100 times in a loop must be structurally impossible. Budget overrun requires the student to manually edit `.env` — not something she can do by accident in the UI.

---

## 6. Technical architecture

### 6.1 Stack

- **Python 3.11+** (Roula's Mac may ship with 3.9 Apple-supplied — install `python@3.11` via Homebrew or python.org installer)
- **Streamlit** — web dashboard framework
- **Plotly** — interactive charts (candlestick, sparkline, radar)
- **yfinance** — Yahoo Finance data (primary source, no API key)
- **requests** — HTTP calls to Finnhub / Alpha Vantage
- **python-dotenv** — `.env` key loading
- **anthropic** — Claude API (optional, for AI briefing tab)

### 6.2 Data source strategy — cascade with graceful fallback

For every data field the dashboard displays, define a cascade:

```
Field → [Primary source, Secondary source, Fallback display]
```

Example:
- **Current price:** yfinance → Finnhub `/quote` → "Price unavailable"
- **Recent news:** Finnhub `/company-news` → Alpha Vantage News → "News not configured. Add Finnhub key to unlock."
- **Earnings date:** Finnhub `/calendar/earnings` → yfinance earnings_dates → "Earnings data unavailable"
- **AI briefing:** Claude API → "Set up AI briefings by adding ANTHROPIC_API_KEY to .env"

Each data_source module implements the same interface. The dashboard calls a central `DataOrchestrator` that tries sources in order and returns the first success.

### 6.3 Why yfinance as primary

- No API key needed — eliminates the entire failure class that killed the previous lesson
- Covers all 5 tickers reliably (US stocks, ETF, Chinese ADR)
- Includes fundamentals, historical data, company info in one library
- Stable, widely used, good Python ergonomics

### 6.4 Why Finnhub as secondary (optional)

- Student already has a Finnhub key (we're solving for using it properly this time)
- Better news feed than yfinance
- Cleaner earnings calendar
- Not required for the tool to work — just enhances it

### 6.5 Why Alpha Vantage as tertiary (optional)

- Pure redundancy — if Finnhub fails AND we want a feature Finnhub provided, Alpha Vantage is the third line
- Free tier: 25 calls/day, 5/minute — fine for backup use
- Not used unless Finnhub is down

### 6.6 The .env strategy (prevents the previous failure)

This is where the previous lesson broke. Prevent it structurally:

1. **`.env.example` is the canonical template** — checked into git, has every key documented with comments explaining what each unlocks and which tier is free
2. **First-run setup script (`setup_check.py`)** — the student's agent runs this after install. It:
   - Checks Python version is 3.11+
   - Confirms `.env` file exists (not `.env.txt` from Notepad on Windows, or `.env.rtf` from TextEdit on macOS — both traps surface clearly)
   - Validates each key if present (hits a minimal endpoint, reports success/failure with friendly message)
   - Tests yfinance with one ticker call
   - Prints a "✅ Ready to run — now say to your agent: 'Start the dashboard'" message
3. **In the Streamlit app itself** — if a key is missing, the relevant tab/feature shows a clear inline instruction telling the student what to say to her agent
4. **No silent failures** — every missing key or broken call surfaces a helpful message, never a stack trace

---

## 7. Repository structure

```
equity-research-desk/
├── README.md                     # For student — what to say to her agent
├── CLAUDE.md                     # For the in-project agent — how this code works
├── PROMPTS.md                    # Cookbook of example prompts for the student
├── PRD.md                        # This file — kept for reference
├── requirements.txt              # pip install -r
├── .env.example                  # Template with every key documented
├── .gitignore                    # Excludes .env, __pycache__, briefings/
├── app.py                        # Streamlit entry point
├── setup_check.py                # Validates environment, runs on first setup
├── config/
│   ├── tickers.yaml              # Watchlist (5 tickers seeded)
│   ├── theme.py                  # Dark theme + custom CSS
│   └── settings.py               # Config loading, env parsing
├── data_sources/
│   ├── __init__.py
│   ├── base.py                   # Abstract base class for data sources
│   ├── yfinance_source.py        # Primary (no key)
│   ├── finnhub_source.py         # Secondary (optional)
│   ├── alphavantage_source.py    # Tertiary (optional)
│   └── orchestrator.py           # Cascade logic
├── views/
│   ├── __init__.py
│   ├── overview.py               # Watchlist overview tab
│   ├── ticker_detail.py          # Per-ticker detail tab
│   ├── comparison.py             # Side-by-side comparison tab
│   ├── briefing.py               # AI briefing tab (uses Claude API)
│   └── settings.py               # Settings tab
├── components/                   # Reusable Streamlit components
│   ├── __init__.py
│   ├── metric_card.py            # Metric with delta indicator
│   ├── sparkline.py              # Mini-chart for watchlist rows
│   └── candlestick_chart.py      # Plotly candlestick + volume
├── lib/
│   ├── __init__.py
│   ├── formatting.py             # Number formatting ($1.5B, +2.3%, etc.)
│   └── cache.py                  # Streamlit caching wrappers
├── briefings/                    # AI briefings land here, gitignored
│   └── .gitkeep
└── tests/
    ├── test_yfinance_source.py   # At least one smoke test
    └── test_orchestrator.py      # Cascade fallback works
```

### 7.1 File purpose summary (quick reference)

| File | Purpose | Audience |
|---|---|---|
| README.md | Setup instructions phrased as prompts | Student (via copy-paste to her agent) |
| CLAUDE.md | Code map, conventions, extension patterns | In-project agent |
| PROMPTS.md | Cookbook of natural-language prompts | Student |
| PRD.md | This file, for context | In-project agent + Sean |
| .env.example | Template with documented keys | Student copies this to .env |
| app.py | Streamlit entry | App runner |
| setup_check.py | First-run validator | Student's agent runs this |

---

## 8. PROMPTS.md specification

A curated list of natural-language prompts the student can say to her Claude Code agent. Grouped by task. Each prompt is a complete sentence she can paste verbatim. The file teaches her by example.

### Sections in PROMPTS.md

**Getting started**
- "Clone this repo and get it running for me: [GITHUB_URL]"
- "I want to use this equity research tool. Can you set it up?"
- "Check if the setup is working and let me know what I need to do next."

**Using the dashboard**
- "Start the dashboard"
- "Stop the dashboard"
- "Refresh the data"

**Managing the watchlist**
- "Add TSLA to my watchlist"
- "Remove BABA from my watchlist"
- "What stocks am I tracking right now?"

**Adding API keys**
- "Help me add my Finnhub API key to the project."
- "Help me add my Claude API key so I can get AI briefings."
- "I have an Alpha Vantage key. Can you wire it up?"

**Customizing views**
- "Add a sector breakdown chart to the comparison tab."
- "Make the charts use monthly data instead of daily by default."
- "I want to see the highest-P/E stocks first in the overview table."

**Troubleshooting**
- "The dashboard isn't loading. Can you figure out what's wrong?"
- "My Finnhub key isn't being recognized. Help me debug."
- "Check why the news section is empty."

**Extending the tool**
- "Add Alpha Vantage as another data source for earnings dates."
- "Create a new tab that shows dividend history for each stock."
- "Can you add a watchlist for ETFs separate from my individual stocks?"

Each prompt should link to or reference the underlying code pattern the agent would use to fulfill it. This is what makes the student's agent effective from session one.

---

## 9. CLAUDE.md specification (in-project agent doc)

This file sits at the project root. When the student opens Claude Code in her cloned project, Claude Code reads this on session start and understands:

1. **What this project is** — 1 paragraph
2. **Who the user is** — Roula, non-technical, operates via prompts
3. **Code map** — what lives in each folder, how the pieces connect
4. **Conventions** — how to name files, how to structure data source modules, how to structure view modules, how to handle errors
5. **Extension patterns** — specifically, how to add:
   - A new ticker (edit `config/tickers.yaml`)
   - A new data source (create `data_sources/<name>_source.py` implementing the base interface, register in orchestrator)
   - A new view / tab (create `views/<name>.py`, register in `app.py`'s tab list)
   - A new chart component (create in `components/`, import where used)
6. **Key safety** — `.env` is gitignored, never commit keys, use `.env.example` for new keys
7. **OS gotchas** — macOS (`python3` vs `python`, TextEdit rich-text default, Finder extension-hiding, Homebrew install paths) first; Windows (`.env.txt` Notepad trap, `py` launcher, PowerShell vs bash) as secondary aside
8. **When to ask the user** — bullet list of decisions the agent should run past Roula before acting (e.g. "before changing the theme or adding a paid API key")
9. **What not to do** — e.g. "don't hardcode API keys in source files, don't commit `.env`, don't add Anthropic calls outside the briefing module"

---

## 10. Setup flow (what happens when her agent gets the GitHub link)

1. Student says to her Claude Code: *"Clone this repo and get it running: [url]"*
2. Agent runs `git clone`, `cd` into folder, opens `CLAUDE.md` and `README.md`
3. Agent runs `pip install -r requirements.txt`
4. Agent checks for `.env`; if absent, copies `.env.example` to `.env` and reports: *"I've created a .env file from the template. You can run the dashboard now with just yfinance (no key needed). If you want more features later, let me know about any API keys."*
5. Agent runs `python setup_check.py` — validates environment, reports status
6. Agent runs `streamlit run app.py` — dashboard opens in her browser
7. Agent tells her: *"Your dashboard is running at http://localhost:8501. Your 5 stocks are loaded. Try saying things like 'add TSLA' or 'show me my comparison view'."*

Elapsed time from clone to live dashboard: target < 3 minutes on macOS (assuming Python 3.11+ and Git are already installed). Add 5-10 min if `brew install python@3.11` or Xcode command-line tools need to run first.

---

## 11. Extensibility framework — how she iterates

The PRD's promise is: once the base tool is shipped, she can say natural things to her agent and the agent extends the tool by following the documented patterns.

### Pattern: Add a new data source

1. Create `data_sources/<name>_source.py`
2. Implement the `DataSource` base class:
   - `get_quote(ticker)`
   - `get_fundamentals(ticker)`
   - `get_news(ticker)`
   - `get_earnings(ticker)`
3. Add to orchestrator's cascade list
4. Add any needed API key to `.env.example` with a comment explaining what it unlocks
5. Test with one call

### Pattern: Add a new view / tab

1. Create `views/<name>.py` with a `render()` function
2. Import in `app.py`
3. Add tab to the tab list
4. Use existing `components/` where possible; create new components in `components/` if needed
5. Follow existing view modules as templates

### Pattern: Add a new component

1. Create `components/<name>.py` with a function that takes data and returns a Streamlit component
2. Use Plotly for any chart needs
3. Follow existing components as templates

### Pattern: Change theme / styling

1. Edit `config/theme.py` — contains color palette, custom CSS
2. Streamlit dark theme is the base; overrides are CSS

### Pattern: Add a new ticker

1. Edit `config/tickers.yaml`
2. Reload dashboard

**All these patterns are documented in CLAUDE.md with example code from the existing codebase so the in-project agent follows them consistently.**

---

## 12. Guardrails and failure modes

### 12.1 The `.env` extension-hiding trap (prevent the previous failure)

- Ship `.env.example` — student's agent copies it to `.env`, never creates one from scratch.
- `setup_check.py` explicitly tests for `.env.txt` (Windows Notepad trap) and reports if found. The macOS equivalent (`.env.rtf` from TextEdit) is caught by the same "verify actual filename" discipline — the agent should `ls -la` (macOS) or `dir /A .env*` (Windows) to see real filenames rather than trust Finder/Explorer's hidden-extension display.
- README + HELP.md tell the student's agent: never ask Roula to edit `.env` in a GUI text editor (TextEdit on Mac, Notepad on Windows). Always edit via the agent's own file tools, or `nano`/`code` from Terminal.

### 12.2 The browser CORS trap (the earlier HTML approach)

- We're using Python + Streamlit, not browser JavaScript → CORS issue doesn't apply
- Document this decision in CLAUDE.md so the agent doesn't accidentally regress to browser-fetched data

### 12.3 API key validation

- `setup_check.py` validates each present key with a minimal endpoint call
- Invalid keys produce friendly error: *"Your Finnhub key was rejected. Possible causes: key not activated (wait 5 min and re-run), wrong value in .env, or free tier exhausted."*

### 12.4 Network failures

- All data source calls wrapped with timeouts (10s default)
- Failed calls logged + displayed in UI, never crash the app
- If all sources fail for a ticker, that row shows "Data unavailable" with a "Retry" button

### 12.5 Claude API usage

See **§5.6 Anthropic API budget protection** for the full spec. Summary:

- Only invoked on explicit user action, never on page load or rerun
- Monthly budget cap enforced structurally (default $5/month, adjustable via `.env`)
- Per-call cost disclosed and confirmed before every call
- Rate-limited (default 1/hour)
- Usage tracked in append-only JSONL ledger
- Same-day caching prevents duplicate spend
- Budget overrun requires manual `.env` edit — cannot happen via the UI

### 12.6 No secrets in git

- `.gitignore` explicitly excludes `.env`, `briefings/*.md`, any `*.key` files
- Pre-commit hook (optional, stretch) to detect accidental key commits

---

## 13. Implementation phases

Each phase is shippable. The student can use the tool at the end of any phase; subsequent phases add capability and polish.

### Phase 0 — Repo scaffold (build this first)
- Create folder structure per §7
- Write `README.md`, `CLAUDE.md`, `PROMPTS.md`, `.env.example`, `.gitignore`, `requirements.txt`
- Seed `config/tickers.yaml` with CRDO, HIMS, BABA, QQQI, IREN
- Empty stubs for all modules
- `setup_check.py` with basic Python version + `.env` existence check

### Phase 1 — Working MVP with yfinance only
- `data_sources/yfinance_source.py` fully implemented
- `data_sources/orchestrator.py` with yfinance as only source
- `app.py` with tab navigation
- `views/overview.py` — watchlist table with live prices
- `views/ticker_detail.py` — basic per-ticker view with price + key metrics + line chart
- At end of Phase 1, student can clone, run, and see her 5 stocks with live data

### Phase 2 — Visual polish (the "looks premium" pass)
- `config/theme.py` — dark theme, custom colors
- `components/metric_card.py` — proper cards with delta indicators
- `components/sparkline.py` — inline mini-charts for watchlist
- `components/candlestick_chart.py` — Plotly candlestick with volume, timeframe toggles
- Update `views/overview.py` and `views/ticker_detail.py` to use these components
- Loading states, color-coding, typography pass

### Phase 3 — Enrichment with Finnhub + Alpha Vantage
- `data_sources/finnhub_source.py` — news, earnings, with error handling
- `data_sources/alphavantage_source.py` — backup fundamentals
- Orchestrator cascade logic
- `views/comparison.py` — all 5 tickers side by side with radar chart + YTD bars
- News panel in ticker_detail view
- Earnings calendar in ticker_detail view

### Phase 4 — AI Briefing tab (uses Claude API)
- `views/briefing.py` with the "Generate briefing" button
- Claude API integration (Sonnet 4.6)
- Markdown output + caching to `briefings/YYYY-MM-DD.md`
- Settings tab entry for `ANTHROPIC_API_KEY`

### Phase 5 — Docs completion
- `CLAUDE.md` finalized with extension patterns and pointers to real code
- `PROMPTS.md` finalized with ~30 prompts across task categories
- README polished for agent-operated flow
- `setup_check.py` expanded with all API key validations

### Phase 6 — Testing + polish
- Fresh-clone smoke test on a separate machine (target: macOS like Roula's; Windows second-pass for Sean's own testing), run through setup flow as a non-technical user
- Error state review (every error path has a helpful message)
- Smoke tests committed

---

## 14. Stretch features (future iterations, not v1)

- Historical watchlist snapshots — weekly portfolio state saved
- Alerts (email / Telegram) when a stock drops X%
- Backtest tool — pick a strategy, see historical returns
- Options data tab (Finnhub has options chains on some tiers)
- Dividend history and projections tab
- Sector breakdown view
- Correlation matrix between her holdings
- Export briefing to PDF
- Multi-portfolio support (e.g. "my stocks" vs "watchlist")
- Mobile-responsive layout tweaks

Mention these in the README so Roula knows the tool has room to grow — she should feel empowered to add them by asking her agent.

---

## 15. Constraints and non-goals

- **Not a trading platform.** No order entry, no broker integration, no portfolio balance tracking with shares owned. Just research and monitoring.
- **Not real-time streaming.** Data refreshes on page load or manual refresh. 15-min delayed is fine.
- **Not multi-user.** Single-user local app. No auth, no user management.
- **Not hosted.** Runs on her laptop, not deployed anywhere. She doesn't need to worry about servers, domains, or hosting costs.
- **No crypto.** Explicitly excluded.
- **No options trading features in v1.** Possibly stretch.
- **No automated trading signals / algorithmic recommendations.** This is a research tool, not an advisor. The AI briefing is analysis, not a recommendation.
- **Not an educational tool.** It's a product. Learning happens when Roula asks her agent to modify it, not through tutorials in the UI.

---

## 16. Decisions locked + remaining open questions

### Locked by Sean 2026-04-21

1. **Repo visibility — PUBLIC** at `github.com/seanmccloskey10-cell/equity-research-desk`.
   - **Rationale:** A private repo would force Roula through GitHub auth (PAT or SSH keys) to clone — friction she can't handle without Sean walking her through it, and every future student hits the same wall. Public removes friction entirely: her agent runs `git clone <url>` with no auth. Nothing sensitive is in the repo itself — `.env` is gitignored, there are no secrets in source. The code being public is a feature, not a risk: future students benefit, Sean gets authorship attribution, and the template pattern (§16.7) only works cleanly with public.
2. **README audience — the agent.** The README is written for Roula's Claude Code agent to parse, not for her to read. Be as technical as needed (exact commands, paths, versions, code examples). Clarity for the agent > readability for humans. Roula will only ever type something like *"Clone this and set it up for me: <url>"* — her agent reads the README and executes.
3. **Claude model — Sonnet 4.6** (`claude-sonnet-4-6`). Locked. See §5.5 and §5.6 for cost-control mechanisms.
4. **Anthropic API safeguards — non-negotiable.** Default budget cap $5/month, per-call confirmation dialog, rate-limited 1/hour, no background calls, structural enforcement. Full spec at §5.6.

### Still open — builder agent can make reasonable defaults or surface to Sean

5. **Python version minimum.** Default 3.9+, can push to 3.11+ if needed for any dependency.
6. **Streamlit theme.** Dark default recommended, toggleable to light.
7. **Live demo deploy.** Out of scope per §15 — not doing it unless Sean explicitly asks.
8. **GitHub template marker.** After v1 ships, mark the repo as a GitHub template so future students click "Use this template" to make their own fork. Do this at ship time.
9. **Testing rigor.** Smoke tests only — orchestrator cascade and yfinance fetch. Nothing more.

---

## 17. Notes for the building agent

- **Start with Phase 0 + Phase 1.** Get a working MVP with yfinance before adding any other data sources. Every phase must leave the tool in a usable state.
- **Write code the student's agent can read.** Prefer explicit over clever. Comments where non-obvious. Type hints where helpful.
- **Follow patterns consistently.** Once you've written one view module, the others follow the same shape. Same for data sources and components. This is what makes the extensibility promise real.
- **Keep `CLAUDE.md` and `PROMPTS.md` synced with reality.** Update them as you build so they always match what's shipped.
- **Test the fresh-clone flow at the end.** Imagine a non-technical user just ran `git clone` — does everything work with zero friction?
