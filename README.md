# FX Research Desk

A local-first FX research dashboard — Python + Streamlit + Plotly, powered by yfinance (no API key required for live FX rates). Zero-key start; AI Briefings unlock when an Anthropic API key is added.

> **Audience note.** This README is written for an AI coding agent (Claude Code) to parse and execute. The user is an **FX research professional** — AI-fluent and a heavy Cowork user, but **not a developer**. They'll say things like *"Clone this and set it up for me."* They have Bloomberg (or comparable real-time market data) — this tool is the synthesis layer over data they already have, not a replacement for it. Clarity for the agent beats prose for a human reader.
>
> **This repo is forked from a prior `equity-research-desk` template** (2026-04-24). The architecture and bootstrap flow are identical; the watchlist, briefing register, and audience are FX-shaped. Most of this README is inherited verbatim — only the data + register sections diverge.

---

## Tech stack

- Python 3.11+
- Streamlit ≥ 1.31 (uses `st.dialog` in Phase 4)
- yfinance — primary data source, no key
- Plotly — charts
- Optional: Finnhub (news + earnings), Alpha Vantage (backup fundamentals), Anthropic Claude Sonnet 4.6 (AI briefings, Phase 4)

---

## Bootstrap — for an agent setting this up on a fresh machine

The user is on **macOS**. They're AI-fluent and won't be intimidated by a terminal, but they're still not a developer — handle setup, config, and any code-level changes yourself via natural-language requests. If a prerequisite is missing, install it yourself (with their one-time consent per install command). Work through these steps **in order**. Stop and ask for help **only** if all automated paths fail.

> **If you're running this on Windows** (e.g. testing from a dev machine), swap `python3` for `python` (or `py`), and use `winget` in place of `brew`. Specific Windows equivalents are listed in the "Windows notes" section below.

### Step 0 — Pre-flight: macOS permissions the user will see (READ THIS FIRST)

Before triggering any installs, **pre-warn the user** about the standard macOS permission dialogs they'll see. macOS pops up several security/permission prompts during a fresh dev environment setup; if they arrive without warning, they slow progress and create friction (captured from prior user research, 2026-04-24).

**Tell the user up front, in plain English:**

> *"You're going to see a few popups from macOS. They're all normal Apple security checks — none of them are unsafe. Click Allow / Open / Install for each one. Here's what to expect:"*

| Popup | What it is | What to click |
|---|---|---|
| **"The git command requires the command line developer tools — would you like to install them now?"** | First-time Git use triggers Xcode CLT install (~5 min download). One-time per machine. | **Install** |
| **"Terminal would like to access files in your Documents/Desktop folder"** | macOS asks before any Terminal-launched process can read those folders. | **OK** / **Allow** |
| **"VS Code would like to access files in your folder"** | Same as above, for VS Code. | **OK** / **Allow** |
| **".pkg installer is from an unidentified developer — would you like to open it?"** | Only if downloading the official Python `.pkg` from python.org. The signed installer is safe; this is just Gatekeeper double-checking. | **Open** (right-click `.pkg` → Open if Gatekeeper blocks the standard double-click) |
| **macOS asks for the user's password** (during install) | Standard system-level install requesting admin rights. | **Use the GUI dialog** (the one with the lock icon — see Step 1 note below) |

### Step 1 — Verify / install Python 3.11+ (GUI-first, password-safe)

macOS ships with an older Apple-supplied Python; you need 3.11 or newer.

**For non-technical users (the user and similar): prefer the official `.pkg` installer.** The `.pkg` installer triggers Apple's standard GUI password dialog (the one with the lock icon) when admin rights are needed. This is much safer-feeling than typing a password into a black Terminal window — important UX point captured from prior user research (2026-04-24): *terminal sudo password entry was uncomfortable; GUI password popup was fine.* Same security, very different feel.

```bash
# Check first — macOS should have python3 as a command:
python3 --version

# If missing, or version is < 3.11, the recommended install for a non-technical user is:
#   1. Open https://www.python.org/downloads/ in Safari/Chrome
#   2. Click the macOS download for Python 3.11 or 3.12 (a .pkg file lands in Downloads)
#   3. Double-click the .pkg → walk through the installer
#      → macOS asks for the user's password via the standard GUI dialog (lock icon) — they enter it there
#      → the installer adds python3 to PATH automatically
#   4. Restart Terminal so PATH picks up the new python3
```

**Why .pkg over Homebrew for non-technical users:** The Homebrew bootstrap (`/bin/bash -c "$(curl ...)"`) asks for the user's password in Terminal. Non-technical users are typically uncomfortable typing their password into a black box where they can't see what they're typing. The GUI dialog feels safe (it's the same Apple-managed dialog they see when installing any signed app); the Terminal password prompt does not. Even though both are technically equivalent, the trust gap is real.

**Homebrew is the better option for technical users** (Sean) or once the user has installed Homebrew once via the GUI bootstrap. If Homebrew is already present:

```bash
brew --version
# If installed, this is fast and clean:
brew install python@3.11
```

**Avoid `curl | bash` style installers in non-technical user sessions.** Same reasoning — the password lands in Terminal, and the user can't see what's being installed.

### Step 2 — Verify / install Git

macOS doesn't ship Git by default but triggers an install prompt the first time you run `git`.

```bash
git --version
# If Git is missing, macOS pops up a dialog: "The git command requires the command line developer tools."
# Click Install. Takes ~5 minutes.

# Alternatively, if Homebrew is available:
brew install git
```

### Step 3 — Clone the repo

```bash
# Clone into the user's Projects folder (create if missing)
mkdir -p ~/Projects && cd ~/Projects
git clone https://github.com/seanmccloskey10-cell/exotic-fx-research-desk
cd exotic-fx-research-desk
```

### Step 4 — One-command setup

```bash
python3 run.py setup
```

That's it. `run.py` handles:

- Creating a local `.venv` (isolated — does not touch the user's other Python projects)
- Installing `requirements.txt` into the venv
- Copying `.env.example` to `.env` if missing
- Running `setup_check.py` (validates Python, deps, `.env`, and does a yfinance live smoke test)

### Step 5 — Start the dashboard

```bash
python3 run.py start
```

Open <http://localhost:8501> in the user's browser (macOS: `open http://localhost:8501` opens the default browser). Tell them the dashboard is running.

### Step 6 — Stop the dashboard (later)

```bash
python3 run.py stop
```

---

## Daily commands the agent should recognize

Everything routes through `run.py` so the agent never has to remember venv paths.

| User says | Agent runs (macOS) | Agent runs (Windows) |
|---|---|---|
| "Start the dashboard" | `python3 run.py start` | `python run.py start` |
| "Stop the dashboard" | `python3 run.py stop` | `python run.py stop` |
| "Refresh the data" | Click the sidebar refresh button; OR stop + start | (same) |
| "Check if setup is working" | `python3 run.py setup` | `python run.py setup` |
| "Run the tests" | `python3 run.py test` | `python run.py test` |
| "Add USDPLN to my watchlist" | Append to [config/tickers.yaml](config/tickers.yaml) under `tickers:`, then tell user to hit Refresh | (same) |
| "Remove X from my watchlist" | Remove from [config/tickers.yaml](config/tickers.yaml) | (same) |
| "Help me add my Finnhub key" | Edit `.env`, set `FINNHUB_API_KEY=<value>`, then restart dashboard | (same) |

More prompts in [PROMPTS.md](PROMPTS.md).

---

## macOS notes — read before first setup

1. **Use `python3`, not `python`.** On macOS, `python` either doesn't exist or points to an old Apple-supplied Python 2/3.9. All commands in this repo use `python3` on macOS.

2. **TextEdit's rich-text default.** If the agent needs to edit `.env` by hand, don't open it in TextEdit — by default TextEdit saves `.rtf`, not plain text. Use VS Code (`code .env`) or `nano .env` in Terminal instead. Better: the agent should edit `.env` directly via its file-editing tools, never hand-off to the user.

3. **Finder extension-hiding.** macOS Finder hides file extensions by default for recognised types. A file that looks like `.env` in Finder might actually be `.env.rtf` on disk. Verify in Terminal with `ls -la` — it shows the real name.

4. **Homebrew is the default package manager.** Most open-source Mac tools assume Homebrew is installed. If the user doesn't have it, install it (step 1) — it's a one-time setup that makes every future install trivial.

5. **`.DS_Store` files.** macOS Finder sprinkles these everywhere. `.gitignore` already excludes them — nothing to worry about.

6. **First-run Gatekeeper prompt.** Python scripts don't trigger Gatekeeper (the unsigned-binary blocker), so this isn't a concern here. Relevant only if installing downloaded apps.

---

## Windows notes (for Sean testing, or future Windows students)

If you're running this on Windows instead of macOS:

1. **Command swap.** Use `python` (or `py`) instead of `python3`. The `run.py` wrapper handles cross-platform venv paths internally; only the launching command differs.

2. **Python install.** `winget install -e --id Python.Python.3.11` (Windows 11 has `winget` by default). Fallback: <https://www.python.org/downloads/> — tick **"Add Python to PATH"** at the top of the installer.

3. **Git install.** `winget install -e --id Git.Git`. Fallback: <https://git-scm.com/download/win>.

4. **Hidden `.txt` extension.** File Explorer hides known extensions. If `.env` is ever opened in Notepad, Windows may save it as `.env.txt`. `setup_check.py` detects this trap. Fix: agent uses `copy .env.example .env` via the CLI so the file is never Notepad-mangled.

5. **`pip` not on PATH.** Don't call `pip` directly. `run.py` uses `.venv/Scripts/python.exe -m pip`, which always works.

6. **`python` vs `py`.** If `python --version` fails but `py --version` works, use `py run.py ...` — happens when Python was installed via the Microsoft Store; the `py` launcher ships with standard Python installers.

7. **PowerShell vs cmd vs bash.** All project commands route through `python run.py <cmd>`, which works identically in any terminal.

---

## Where to learn the code

Agent: read [CLAUDE.md](CLAUDE.md) before modifying anything. Code map, extension patterns, and the non-negotiable rules (Settings tab is read-only, Anthropic calls only from `views/briefing.py`, etc.).

**When something breaks**: [HELP.md](HELP.md) is the first stop — it has a single prompt you paste to your agent that runs a full diagnostic across Python, `.env`, keys, dashboard, and connectivity. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) is the deeper reference for specific failure recipes.

Everyone: [PRD.md](PRD.md) is the full spec. [APIS.md](APIS.md) is the menu of additional data sources the user can add.

---

## Current build status

- **Phase 0** — scaffold ✅
- **Phase 1** — yfinance MVP ✅ (Overview + Detail tabs live)
- **Phase 2** — visual polish ✅ (candlestick + volume, inline sparklines, custom CSS theme)
- **Phase 3** — Finnhub + Alpha Vantage + Comparison tab ✅ (news/earnings unlock with Finnhub key)
- **Phase 4** — AI Briefing with full §5.6 budget protection ✅ (confirmation dialog, rate limit, hard cap, usage ledger, same-day cache)
- **Phase 5** — docs completion + more prompts ✅ (TROUBLESHOOTING.md + expanded PROMPTS.md)
- **Phase 6** — fresh-clone smoke test + polish — pending
