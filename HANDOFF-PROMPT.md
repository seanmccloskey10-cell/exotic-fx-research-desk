# HANDOFF-PROMPT.md — Paste this into Claude Code

Copy everything between the lines below and paste it in one shot to your AI agent in VS Code (Claude Code). The agent will install and configure the dashboard for you.

The prompt instructs the agent to:
- **Enter plan mode FIRST** — propose what it'll do before running anything
- **Recognize the OS handoff** — this tool was built and tested on a Windows machine; the user is on a Mac, so the agent must adapt commands accordingly
- **Pre-warn about macOS permission popups** — no surprise dialogs mid-execution
- **Use Apple's GUI password dialog, NEVER terminal sudo** — same security, much better UX
- **Read README.md and CLAUDE.md** before running anything
- **Verify "what done looks like" with concrete checks** — no false-positive "it's working" claims
- **Flag any residual Roula-isms** — this repo was forked from Roula's `equity-research-desk` so a Mac agent setting it up clean may spot small things to fix

---

## The prompt — paste everything between the lines below

---

```
Someone built me a small FX research dashboard they want me to install
on my Mac. I work in FX research and I'm AI-fluent (heavy Cowork user),
but I'm not a developer — I won't type commands, edit code, or debug
stack traces. You handle setup, config, and any code-level adjustments
via natural-language requests from me.

I want you to clone and set up this tool for me:

    https://github.com/seanmccloskey10-cell/exotic-fx-research-desk

It's a local-first FX dashboard — Python + Streamlit + Plotly, powered
by yfinance for live FX rates. It runs entirely on my Mac, nothing leaves
the machine except the optional AI Briefing call (which uses an Anthropic
API key — separate from my Claude plan, billed per-token, hard monthly
cap).

OS HANDOFF — IMPORTANT
This tool was built and dry-run tested on Windows 11. I'm on macOS.
The repo's README has both macOS and Windows install paths, but assume
some commands or examples in the code may carry Windows assumptions.
Catch them as you go and adjust silently — don't ask me what to do
about a `.streamlit.pid` file or whether to use `python` vs `python3`.
The tool's `run.py` wrapper is cross-platform; just use `python3` on
my machine consistently.

Permissions — just a one-time ack from me per install. You'll need
some or all of these depending on what's already on my machine:
- Xcode command-line tools (one-time Apple install dialog, for git)
- Python 3.11+ via the official .pkg installer from python.org
  (uses Apple's standard GUI password dialog with the lock icon —
  never a terminal sudo prompt)
- VS Code (if I don't have it — drag-to-Applications install)
- The repo's Python dependencies (Streamlit, Plotly, yfinance, etc.) —
  these go into a local .venv inside the repo, your run.py setup
  command handles them

I'll say "go" once when you ask. Don't ask again per command.

Please follow this flow:

1. ENTER PLAN MODE FIRST. Tell me:
   - What's already installed on my Mac (run version commands; report what
     you find)
   - What you propose to install
   - Which README steps you'll follow
   - Anything in the repo that looks Windows-specific that you'll need to
     work around on macOS
   Don't start running setup until I say "go".

2. Pre-warn me about macOS popups I'll see during setup, in plain English.
   The common ones:
   - "The git command requires the command line developer tools — install?"
     → Click Install. Takes ~5 minutes.
   - "Python.pkg is from an unidentified developer — open?"
     → Right-click the .pkg → Open if Gatekeeper blocks the standard
     double-click.
   - "Terminal would like to access files in your Documents folder"
     → OK / Allow.
   - macOS asking for my password during install
     → ALWAYS use the Apple GUI password dialog (the one with the lock
     icon). NEVER ask me to type my password into a terminal window.
     Same security, very different feel.

3. Read README.md and CLAUDE.md end-to-end before running anything. The
   README has the full bootstrap walkthrough; the CLAUDE.md has the
   non-negotiable rules and explains how the codebase is organized
   (Settings tab is read-only, Anthropic API calls only from
   views/briefing.py, etc.).

4. Read PRD.md if you need full product context — but PRD.md is inherited
   from the parent repo (Roula's equity-research-desk), so most of it
   describes equities. The PRD has a delta header at the top that explains
   what's different in the FX variant. Don't be confused by the
   equity-specific body text below the delta header — the FX variant is
   what's running.

5. Clone the repo into ~/Projects/exotic-fx-research-desk (create the
   Projects folder if it doesn't exist).

6. Open the cloned folder in VS Code.

7. Run `python3 run.py setup`. This creates a .venv, installs deps, copies
   .env.example to .env, and runs setup_check.py. Report each step.

8. Run `python3 run.py start` to start the dashboard. Then open
   http://localhost:8501 in my browser.

9. Stop when the dashboard is running and the watchlist shows live FX
   rates. DO NOT volunteer to set up the optional Anthropic API key
   for AI Briefings — we'll handle that together in our next
   lesson.

WHAT "DONE" LOOKS LIKE — tell me ONLY when you've verified ALL of these:
- The folder ~/Projects/exotic-fx-research-desk/ exists with README.md,
  CLAUDE.md, PRD.md, run.py, app.py, .venv/, config/tickers.yaml.
- `python3 --version` shows 3.11 or newer.
- `python3 run.py setup` ran to completion with no errors.
- `python3 run.py start` is running; the dashboard is reachable at
  http://localhost:8501.
- The dashboard sidebar shows my watchlist (EUR/USD, USD/TRY, USD/ZAR,
  USD/BRL, USD/MXN, USD/IDR, USD/PHP, USD/VND).
- At least one of those pairs shows a live price (not a dash, not an
  error). yfinance is sometimes patchy on exotic crosses; one good price
  out of eight is enough to confirm the data layer works.
- No red error banners on screen.

If any of those aren't right, don't say "it's working" — stop and tell me
exactly what's off.

A FEW THINGS ABOUT THIS REPO YOU SHOULD KNOW
This repo is a fork of an `equity-research-desk` template (built
originally for equities). The architecture, run.py flow, and tab
structure are identical. The fork swapped:
- The watchlist (stocks → FX pairs)
- The briefing prompt (equity register → macro/FX register)
- The audience copy throughout (Roula → the user)

If you spot residual Roula-isms or stock-specific examples in the docs
or code that the swap missed (especially in PROMPTS.md, HELP.md, or
TROUBLESHOOTING.md, which weren't fully rewritten), flag them to me.
Don't fix them silently — I want to know what's drifted.

Also: there's a known cosmetic gap. The market-session indicator in the
sidebar shows "NYSE" hours, but FX trades 24/5 with London/NY/Tokyo
handoffs. The builder intentionally deferred fixing this until I use
the tool for a week and decide whether session-aware FX context matters.
Don't "fix" it without my approval.

If you hit anything unexpected during setup — network failure, a
dependency install error, a permissions dialog you don't understand,
or anything that asks me to type my password into a terminal — STOP
and ask me before continuing. Don't silently skip or work around
anything.

Report back at each major step. Keep me in the loop.

Let's begin — please enter plan mode and tell me what's on my machine.
```

---

## If you (Sean) ever need to test this on Windows

Same prompt with three swaps:
- "macOS" / "Mac mini" → "Windows 11"
- "python3" → "python" (or "py" if Python Launcher is the install)
- The macOS permission table → Windows UAC + SmartScreen + Defender Firewall warnings (UAC = "Yes", SmartScreen = "More info → Run anyway" if signed installer, Defender = "Allow")
- "Apple GUI password dialog" → "Windows UAC dialog" (same principle: trust the OS-native dialog, never terminal sudo)

The repo's `run.py` and the README's "Windows notes" section already cover the `python` vs `python3` switch, the `winget` installs, the Notepad `.env.txt` trap, and the `taskkill` vs `kill` differences.

## Why this prompt is shaped the way it is

Six lessons baked in from Sean's prior teaching incidents:

1. **Plan mode FIRST.** Without this, an agent on a fresh machine just starts copy-pasting Windows steps onto macOS without thinking. (Sean's [Roula L4 lesson, 2026-04-24](https://github.com/seanmccloskey10-cell/equity-research-desk/blob/main/SESSION-NOTES.md) — the Windows-vs-Mac slip cost ~10 min.)
2. **Permissions ack'd up front.** Surprise OS dialogs mid-execution are friction. Pre-warn, then go.
3. **GUI password dialog, never terminal sudo.** Captured from the same Roula L4 — typing a password into a black box was visibly uncomfortable; Apple's lock-icon dialog felt safe. Same security, different trust feel.
4. **Read README + CLAUDE.md before running.** Without this rule, agents skip context and miss invariants. The Settings-tab-read-only + Anthropic-only-in-views/briefing.py rules in CLAUDE.md are load-bearing safety properties; setting up without reading them risks regression.
5. **"What done looks like" with concrete checks.** Prevents the agent from gaslighting the user that a broken setup is fine.
6. **Don't fix what isn't broken without approval.** The known NYSE-hours gap is intentional — let the user own the timing of fixing it.

## Cross-references

- Pattern source: [Sean's vault — student tool handoff prompt template](https://github.com/seanmccloskey10-cell/Obsidian) (private)
- Sibling repo: [`fx-research-workspace`](https://github.com/seanmccloskey10-cell/fx-research-workspace) — companion deep-research workspace with its own (lighter) handoff prompt
