# HANDOFF-PROMPT.md — Paste this into Claude Code

The fastest way to install this tool: open VS Code on a fresh machine, run `claude` in the terminal to start Claude Code, then paste **one** of the two prompts below into the chat. Pick the one matching your OS. The agent enters plan mode first, tells you what's already on your machine, asks for one "go," then handles the entire setup.

The prompts are **deliberately verbose**. They bake in six lessons from prior user research:

1. **Plan mode FIRST** — the agent must report what it found before installing anything
2. **Permissions ack'd up front** — no surprise dialogs mid-execution
3. **GUI password dialogs / native UAC, NEVER terminal sudo** — same security, different trust feel
4. **Read README + CLAUDE.md before running anything** — the codebase has invariants that matter
5. **"What done looks like"** — the agent verifies concrete checks before claiming success
6. **Don't fix what isn't broken without approval** — known cosmetic gaps stay unless you say otherwise

---

## Mac variant — paste this if you're on macOS

```
Someone built me a small FX research dashboard they want me to install
on my Mac. I work in FX research and I'm AI-fluent (heavy Claude user),
but I'm not a developer — I won't type commands, edit code, or debug
stack traces. You handle setup, config, and any code-level adjustments
via natural-language requests from me.

I want you to clone and set up this tool for me:

    https://github.com/seanmccloskey10-cell/exotic-fx-research-desk

It's a local-first FX dashboard — Python + Streamlit + Plotly, powered
by yfinance for live FX rates. It runs entirely on my Mac, nothing
leaves the machine except the optional AI Briefing call (which uses an
Anthropic API key — separate from any Claude plan, billed per-token,
hard monthly cap).

OS HANDOFF — IMPORTANT
This tool was originally built and dry-run tested on Windows 11. I'm
on macOS. The repo's README has both macOS and Windows install paths,
but assume some commands or examples in the code may carry Windows
assumptions. Catch them as you go and adjust silently — don't ask me
what to do about a `.streamlit.pid` file or whether to use `python` vs
`python3`. The tool's `run.py` wrapper is cross-platform; just use
`python3` on my machine consistently.

Permissions — just a one-time ack from me per install. You'll need
some or all of these depending on what's already on my machine:
- Xcode command-line tools (one-time Apple install dialog, for git)
- Python 3.11+ via the official .pkg installer from python.org
  (uses Apple's standard GUI password dialog with the lock icon —
  never a terminal sudo prompt)
- VS Code (if I don't have it — drag-to-Applications install)
- The repo's Python dependencies (Streamlit, Plotly, yfinance, etc.)
  go into a local .venv inside the repo — your run.py setup command
  handles them

I'll say "go" once when you ask. Don't ask again per command.

Please follow this flow:

1. ENTER PLAN MODE FIRST. Tell me:
   - What's already installed on my Mac (run version commands; report
     what you find)
   - What you propose to install
   - Which README steps you'll follow
   - Anything in the repo that looks Windows-specific that you'll
     need to work around on macOS

   Don't start running setup until I say "go".

2. Pre-warn me about macOS popups I'll see during setup, in plain
   English. The common ones:
   - "The git command requires the command line developer tools —
     install?" → Click Install. Takes ~5 minutes.
   - "Python.pkg is from an unidentified developer — open?"
     → Right-click the .pkg → Open if Gatekeeper blocks the standard
     double-click.
   - "Terminal would like to access files in your Documents folder"
     → OK / Allow.
   - macOS asking for my password during install
     → ALWAYS use the Apple GUI password dialog (the one with the
     lock icon). NEVER ask me to type my password into a terminal
     window. Same security, very different feel.

3. Read README.md and CLAUDE.md end-to-end before running anything.
   The README has the full bootstrap walkthrough; CLAUDE.md has the
   non-negotiable rules and explains how the codebase is organized
   (Settings tab is read-only, Anthropic API calls only from
   views/briefing.py, etc.).

4. Read PRD.md if you need full product context. It's a generic FX
   research dashboard spec — not personalized to any specific user.

5. Clone the repo into ~/Projects/exotic-fx-research-desk (create the
   Projects folder if it doesn't exist).

6. Open the cloned folder in VS Code.

7. Run `python3 run.py setup`. This creates a .venv, installs deps,
   copies .env.example to .env, and runs setup_check.py. Report each
   step.

8. Run `python3 run.py start` to start the dashboard. Then open
   http://localhost:8501 in my browser.

9. Stop when the dashboard is running and the watchlist shows live
   FX rates. DO NOT volunteer to set up the optional Anthropic API
   key for AI Briefings — that's a deliberate add-on for later.

WHAT "DONE" LOOKS LIKE — tell me ONLY when you've verified ALL of these:
- The folder ~/Projects/exotic-fx-research-desk/ exists with
  README.md, CLAUDE.md, PRD.md, run.py, app.py, .venv/,
  config/tickers.yaml.
- `python3 --version` shows 3.11 or newer.
- `python3 run.py setup` ran to completion with no errors.
- `python3 run.py start` is running; the dashboard is reachable at
  http://localhost:8501.
- The dashboard sidebar shows the watchlist (EUR/USD, USD/TRY,
  USD/ZAR, USD/BRL, USD/MXN, USD/IDR, USD/PHP, USD/VND).
- At least one of those pairs shows a live price (not a dash, not
  an error). yfinance is sometimes patchy on exotic crosses; one
  good price out of eight is enough to confirm the data layer works.
- No red error banners on screen.

If any of those aren't right, don't say "it's working" — stop and
tell me exactly what's off.

A FEW THINGS ABOUT THIS REPO YOU SHOULD KNOW
This repo is a fork of an `equity-research-desk` template (built
originally for equities). The architecture, run.py flow, and tab
structure are identical. The fork swapped:
- The watchlist (stocks → FX pairs)
- The briefing prompt (equity register → macro/FX register)
- The audience copy throughout

If you spot residual stock-specific examples in the docs or code that
the swap missed, flag them — don't fix them silently.

Also: there's a known cosmetic gap. The market-session indicator in
the sidebar shows "NYSE" hours, but FX trades 24/5 with London/NY/
Tokyo handoffs. The builder intentionally deferred fixing this. Don't
"fix" it without my approval.

If you hit anything unexpected during setup — network failure, a
dependency install error, a permissions dialog you don't understand,
or anything that asks me to type my password into a terminal — STOP
and ask me before continuing. Don't silently skip or work around
anything.

Report back at each major step. Keep me in the loop.

Let's begin — please enter plan mode and tell me what's on my machine.
```

---

## Windows variant — paste this if you're on Windows

```
Someone built me a small FX research dashboard they want me to install
on my Windows PC. I work in FX research and I'm AI-fluent (heavy Claude
user), but I'm not a developer — I won't type commands, edit code, or
debug stack traces. You handle setup, config, and any code-level
adjustments via natural-language requests from me.

I want you to clone and set up this tool for me:

    https://github.com/seanmccloskey10-cell/exotic-fx-research-desk

It's a local-first FX dashboard — Python + Streamlit + Plotly, powered
by yfinance for live FX rates. It runs entirely on my PC, nothing
leaves the machine except the optional AI Briefing call (which uses an
Anthropic API key — separate from any Claude plan, billed per-token,
hard monthly cap).

OS HANDOFF — IMPORTANT
This tool's README leans Mac-first in its narrative and code examples.
I'm on Windows 11. The repo has a "Windows notes" section and the
`run.py` wrapper is cross-platform, but catch Mac-isms as you go and
adjust silently — don't ask me what to do about `.streamlit.pid` or
whether to use `python3` vs `python`. Use `python` (or `py` if Python
Launcher is what's installed) on my machine consistently.

Permissions — just a one-time ack from me per install. You'll need
some or all of these depending on what's already on my machine:
- Git for Windows (winget install -e --id Git.Git triggers UAC)
- Python 3.11+ (winget install -e --id Python.Python.3.11; if using
  the python.org installer instead, MAKE SURE the "Add Python to
  PATH" checkbox is ticked on the first installer screen)
- VS Code (winget install -e --id Microsoft.VisualStudioCode)
- The repo's Python dependencies (Streamlit, Plotly, yfinance, etc.)
  go into a local .venv inside the repo — your run.py setup command
  handles them

I'll say "go" once when you ask. Don't ask again per command.

Please follow this flow:

1. ENTER PLAN MODE FIRST. Tell me:
   - What's already installed on my Windows machine (run version
     commands; report what you find)
   - What you propose to install
   - Which README steps you'll follow
   - Anything in the repo that looks Mac-specific that you'll need
     to work around on Windows

   Don't start running setup until I say "go".

2. Pre-warn me about Windows dialogs I'll see during setup, in plain
   English. The common ones:
   - UAC ("Do you want to allow this app to make changes?") → click
     Yes. Standard Windows admin permission for an installer.
   - SmartScreen ("Windows protected your PC") → click "More info"
     then "Run anyway" if it's a signed installer from python.org or
     code.visualstudio.com.
   - "Allow Python through Windows Defender Firewall?" → click Allow.
   I will NEVER need to type my password into a terminal. If a step
   asks for that, stop and tell me — that's wrong.

3. Read README.md and CLAUDE.md end-to-end before running anything.
   The README has the full bootstrap walkthrough; CLAUDE.md has the
   non-negotiable rules and explains how the codebase is organized
   (Settings tab is read-only, Anthropic API calls only from
   views/briefing.py, etc.).

4. Read PRD.md if you need full product context. It's a generic FX
   research dashboard spec — not personalized to any specific user.

5. Clone the repo into %USERPROFILE%\Projects\exotic-fx-research-desk
   (create the Projects folder if it doesn't exist).

6. Open the cloned folder in VS Code.

7. Run `python run.py setup`. This creates a .venv, installs deps,
   copies .env.example to .env, and runs setup_check.py. Report each
   step. (If `python` doesn't work, try `py run.py setup` — the
   Windows Python Launcher.)

8. Run `python run.py start` to start the dashboard. Then open
   http://localhost:8501 in my browser.

9. Stop when the dashboard is running and the watchlist shows live
   FX rates. DO NOT volunteer to set up the optional Anthropic API
   key for AI Briefings — that's a deliberate add-on for later.

WHAT "DONE" LOOKS LIKE — tell me ONLY when you've verified ALL of these:
- The folder C:\Users\<me>\Projects\exotic-fx-research-desk\ exists
  with README.md, CLAUDE.md, PRD.md, run.py, app.py, .venv\,
  config\tickers.yaml.
- `python --version` (or `py --version`) shows 3.11 or newer.
- `python run.py setup` ran to completion with no errors.
- `python run.py start` is running; the dashboard is reachable at
  http://localhost:8501.
- The dashboard sidebar shows the watchlist (EUR/USD, USD/TRY,
  USD/ZAR, USD/BRL, USD/MXN, USD/IDR, USD/PHP, USD/VND).
- At least one of those pairs shows a live price (not a dash, not
  an error). yfinance is sometimes patchy on exotic crosses; one
  good price out of eight is enough to confirm the data layer works.
- No red error banners on screen.

If any of those aren't right, don't say "it's working" — stop and
tell me exactly what's off.

A FEW THINGS ABOUT THIS REPO YOU SHOULD KNOW
This repo is a fork of an `equity-research-desk` template (built
originally for equities). The architecture, run.py flow, and tab
structure are identical. The fork swapped:
- The watchlist (stocks → FX pairs)
- The briefing prompt (equity register → macro/FX register)
- The audience copy throughout

If you spot residual stock-specific examples in the docs or code that
the swap missed, flag them — don't fix them silently.

Also: there's a known cosmetic gap. The market-session indicator in
the sidebar shows "NYSE" hours, but FX trades 24/5 with London/NY/
Tokyo handoffs. The builder intentionally deferred fixing this. Don't
"fix" it without my approval.

If you hit anything unexpected during setup — network failure, a
dependency install error, a UAC dialog you don't understand, or
anything that asks me to type my password into a terminal — STOP
and ask me before continuing. Don't silently skip or work around
anything.

Report back at each major step. Keep me in the loop.

Let's begin — please enter plan mode and tell me what's on my machine.
```

---

## Cross-references

- Sibling repo: [`fx-research-workspace`](https://github.com/seanmccloskey10-cell/fx-research-workspace) — companion deep-research workspace with its own (lighter) handoff prompt
