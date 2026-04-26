# HANDOFF-PROMPT.md — Paste this into Claude Code

The fastest way to install this tool: open VS Code on a fresh machine, run `claude` in the terminal to start Claude Code CLI, then paste **one** of the two prompts below into the chat. Pick the one matching your OS. The agent enters plan mode first, tells you what's already on your machine, asks for one "go," then handles the entire setup.

## ⚠ Read this first — install prerequisites before pasting the handoff prompt

The handoff prompts below assume you already have:

- **Git**
- **Python 3.11+**
- **VS Code**
- **Node.js + npm** (Claude Code CLI is installed via npm)
- **Claude Code CLI** (`claude` command in a terminal — *NOT* the VS Code "Claude" extension; they're separate products and the handoff prompt assumes the CLI)
- **Authenticated to a Claude plan** (not via `ANTHROPIC_API_KEY` env var)

**If any of those are missing, run [PREREQUISITES.md](PREREQUISITES.md) FIRST.** The prerequisites prompt batches every install into one elevated session (one UAC popup on Windows, one Apple GUI password dialog on Mac) so you don't drown in permission prompts. It also installs the Claude Code CLI and verifies plan auth before you paste the handoff.

The handoff prompts below check prerequisites at the top. If they're missing, the agent will tell you to go run PREREQUISITES.md first.

The prompts are **deliberately verbose**. They bake in six lessons from prior user research:

1. **Plan mode FIRST** — the agent must report what it found before doing anything
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

PREREQUISITES CHECK — DO THIS FIRST
Before anything else, verify I have the prerequisites installed:
- Git: `git --version`
- Python 3.11+: `python3 --version`
- VS Code: `which code` (NOT bare `code` — that may resolve to a
  Node binary inside VS Code's bundle on some setups)
- Claude Code CLI: `which claude` (NOTE: this is the `claude`
  command in Terminal — distinct from the "Claude" VS Code
  extension. The extension is a chat panel inside VS Code; the CLI
  is a separate npm-installed binary. This handoff prompt was
  designed for the CLI; if I'm currently talking to you through
  the VS Code extension, that's fine for running this prompt, but
  the dashboard install steps below assume the CLI exists.)
- Plan auth (NOT API key): once `claude` runs, it should be using
  my plan login — NOT an `ANTHROPIC_API_KEY` env var. Check
  `echo $ANTHROPIC_API_KEY` (should be empty or unset).

If ANY of those are missing or wrong, STOP and tell me. I'll go run
the prerequisites prompt at PREREQUISITES.md in this same repo
(https://github.com/seanmccloskey10-cell/exotic-fx-research-desk/blob/main/PREREQUISITES.md)
to install them properly in one batch — then come back here.

If all prerequisites are good, proceed:

I'll say "go" once when you ask. Don't ask again per command.

Please follow this flow:

1. ENTER PLAN MODE FIRST. After confirming prerequisites, tell me:
   - Which README steps you'll follow
   - Anything in the repo that looks Windows-specific that you'll
     need to work around on macOS

   Don't start running anything until I say "go".

2. Read README.md and CLAUDE.md end-to-end before running anything.
   The README has the full bootstrap walkthrough; CLAUDE.md has the
   non-negotiable rules and explains how the codebase is organized
   (Settings tab is read-only, Anthropic API calls only from
   views/briefing.py, etc.).

3. Read PRD.md if you need full product context. It's a generic FX
   research dashboard spec — not personalized to any specific user.

4. Clone the repo into ~/Projects/exotic-fx-research-desk (create
   the Projects folder if it doesn't exist).

5. Open the cloned folder in VS Code.

6. Run `python3 run.py setup`. This creates a .venv, installs deps,
   copies .env.example to .env, and runs setup_check.py. Report each
   step.

7. Run `python3 run.py start` to start the dashboard. Then open
   http://localhost:8501 in my browser.

8. Stop when the dashboard is running and the watchlist shows live
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
dependency install error, or anything that asks me to type my
password into a terminal — STOP and ask me before continuing. Don't
silently skip or work around anything.

Report back at each major step. Keep me in the loop.

Let's begin — please run the prerequisites check and tell me what
you find.
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

PREREQUISITES CHECK — DO THIS FIRST
Before anything else, verify I have the prerequisites installed.
USE POWERSHELL for the version checks (NOT bash / git-bash — bash on
Windows resolves some commands differently and gives confusing
output). Specifically:

- Git: `git --version`
- Python 3.11+: `python --version` (and `py --version` as fallback)
- VS Code: `where.exe code` (NOT bare `code --version` — on Windows
  in bash, `code` may resolve to a Node.js binary inside VS Code's
  bundled folder and return a Node version like v22.x. Use
  `where.exe code` to see all candidates and pick the one ending
  in `code.cmd`. Or run `code.cmd --version` directly.)
- Node.js + npm: `node --version` and `npm --version` (Claude Code
  CLI is installed via npm, so npm has to work)
- Claude Code CLI: `where.exe claude` (NOTE: this is the `claude`
  command in a terminal — distinct from the "Claude" VS Code
  extension. The extension is a chat panel inside VS Code; the CLI
  is a separate npm-installed binary. This handoff prompt was
  designed for the CLI; if I'm currently talking to you through
  the VS Code extension, that's fine for running this prompt, but
  the dashboard install steps below assume the CLI exists.)
- Plan auth (NOT API key): once `claude` runs, it should be using
  my plan login — NOT an `ANTHROPIC_API_KEY` env var. Check
  `Get-Item Env:\ANTHROPIC_API_KEY -ErrorAction SilentlyContinue`
  (should return empty).

If ANY of those are missing or wrong, STOP and tell me. I'll go run
the prerequisites prompt at PREREQUISITES.md in this same repo
(https://github.com/seanmccloskey10-cell/exotic-fx-research-desk/blob/main/PREREQUISITES.md)
to install them properly in one batched session — then come back
here.

If all prerequisites are good, proceed.

I'll say "go" once when you ask. Don't ask again per command.

Please follow this flow:

1. ENTER PLAN MODE FIRST. After confirming prerequisites, tell me:
   - Which README steps you'll follow
   - Anything in the repo that looks Mac-specific that you'll need
     to work around on Windows

   Don't start running anything until I say "go".

2. Read README.md and CLAUDE.md end-to-end before running anything.
   The README has the full bootstrap walkthrough; CLAUDE.md has the
   non-negotiable rules and explains how the codebase is organized
   (Settings tab is read-only, Anthropic API calls only from
   views/briefing.py, etc.).

3. Read PRD.md if you need full product context. It's a generic FX
   research dashboard spec — not personalized to any specific user.

4. Clone the repo into %USERPROFILE%\Projects\exotic-fx-research-desk
   (create the Projects folder if it doesn't exist).

5. Open the cloned folder in VS Code.

6. Run `python run.py setup`. This creates a .venv, installs deps,
   copies .env.example to .env, and runs setup_check.py. Report each
   step. (If `python` doesn't work, try `py run.py setup` — the
   Windows Python Launcher.)

7. Run `python run.py start` to start the dashboard. Then open
   http://localhost:8501 in my browser.

8. Stop when the dashboard is running and the watchlist shows live
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
dependency install error, or anything that asks me to type my
password into a terminal — STOP and ask me before continuing. Don't
silently skip or work around anything.

Report back at each major step. Keep me in the loop.

Let's begin — please run the prerequisites check (in PowerShell, not
bash) and tell me what you find.
```

---

## Cross-references

- Sibling repo: [`fx-research-workspace`](https://github.com/seanmccloskey10-cell/fx-research-workspace) — companion deep-research workspace with its own (lighter) handoff prompt
