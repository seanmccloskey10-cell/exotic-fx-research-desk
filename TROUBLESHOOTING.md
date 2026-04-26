# Troubleshooting

Common problems and how to fix them. Written for Roula's Claude Code agent to scan when she describes a problem — paste the symptom into the search box here, the agent executes the fix.

Roula is on **macOS**, so macOS commands are shown first. Windows equivalents are in parentheses where relevant (for Sean testing, or future Windows students).

---

## Setup

### `python3: command not found` (macOS) or `python: command not found` (Windows)

Python isn't installed, or isn't on PATH.

**Fix on macOS:**
```bash
# Install via Homebrew (preferred):
brew install python@3.11

# If Homebrew isn't installed:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
# Then: brew install python@3.11

# No Homebrew, no Terminal install? Download the .pkg installer:
#   https://www.python.org/downloads/
# Double-click to run. It adds `python3` to PATH automatically.
```

**Fix on Windows:**
```powershell
# Try the Python launcher first
py --version
# If that works, use py everywhere instead of python.

# Otherwise, install:
winget install -e --id Python.Python.3.11
# Restart the terminal.
```

### `Python 3.x.x is too old. Need Python 3.11+`

`run.py` detected an older Python.

- **macOS**: The default Python is often 3.9 (Apple-supplied). `brew install python@3.11` and restart Terminal.
- **Windows**: `winget install -e --id Python.Python.3.11` and restart terminal.

### `.env.rtf` exists (macOS) or `.env.txt` exists (Windows)

File was saved with a wrong extension because the OS/editor hid or added it.

- **macOS**: TextEdit's default rich-text format. The agent should edit `.env` via its file tools, not TextEdit. If she already has a `.env.rtf`, delete it; the agent will re-copy `.env.example` → `.env` on next `python3 run.py setup`.
- **Windows**: Notepad + Explorer's hidden-extension trap. Same fix — delete the `.env.txt` and re-run setup.

**Never ask Roula to edit `.env` in any GUI text editor by hand.**

### `pip install` fails with permission error

Don't run as admin/sudo. Make sure the install is going into the venv, not system Python. `run.py` handles this — always use `python3 run.py setup` (or `python run.py setup` on Windows), never a bare `pip install`.

### `run.py setup` runs forever / appears to hang

First-run installs take 60–90 seconds (streamlit + yfinance + plotly are large). If it exceeds 3 minutes, kill the terminal (Ctrl+C) and re-run — pip may be stuck on a slow mirror. Check internet connection if it happens twice.

---

## Running the dashboard

### `Dashboard already running (PID X)` but browser shows nothing

The `.streamlit.pid` file is stale — the process is gone but the file wasn't cleaned up.

**Fix:**
```bash
# macOS:
python3 run.py stop
python3 run.py start

# Windows:
python run.py stop
python run.py start
```

### `Port 8501 already in use`

Another app (or a leftover Streamlit process) is on the port.

**Fix on macOS:**
```bash
# Find what's using port 8501
lsof -i :8501

# Kill it by PID (replace 12345 with actual PID)
kill -9 12345

# Restart
python3 run.py start
```

**Fix on Windows:**
```powershell
# Find what's using it
netstat -ano | findstr :8501

# Kill it by PID
taskkill /PID <pid> /F

# Restart
python run.py start
```

### Dashboard opens but the page is blank

Usually a Python error during view render.

**Fix on macOS:**
```bash
python3 run.py stop
# Run streamlit in the foreground so errors surface:
./.venv/bin/python -m streamlit run app.py
# Read the red stack trace, fix the view file, restart:
python3 run.py start
```

**Fix on Windows:**
```powershell
python run.py stop
.\.venv\Scripts\python.exe -m streamlit run app.py
python run.py start
```

### Every ticker shows `—` for price / metrics

yfinance is temporarily unavailable. Not a bug. Click **Refresh** in the sidebar. If still empty after 5 min, Yahoo Finance may be throttling — try again in an hour.

The Overview tab shows an explicit error banner when all tickers fail. If you see that banner, no action is needed other than waiting or checking network connectivity. If Roula is on a corporate VPN (common for GE), try disconnecting and retry.

---

## API keys

### Added my Finnhub key but the sidebar still shows ⚪ `finnhub`

Streamlit cached the "no key" state. Restart:
```bash
# macOS:
python3 run.py stop && python3 run.py start

# Windows:
python run.py stop && python run.py start
```

### `setup_check.py` reports the key as detected, but news/earnings panels say "add your Finnhub key"

Same as above — restart. Streamlit reads `.env` at app boot.

### Invalid Finnhub key rejected

Possible causes, in order of likelihood:
1. Key not activated yet (fresh signups take ~5 min — wait and retry)
2. Copy-paste picked up whitespace — open `.env`, remove spaces around the `=`
3. Wrong value pasted — check <https://finnhub.io/dashboard>
4. Free tier exhausted (60 calls/min — unlikely for personal use)

### Alpha Vantage returning no data

Free tier is 25 calls/**day**, 5/minute. If you've been using it heavily, it's rate-limited for the day. The orchestrator automatically falls back to yfinance so the dashboard keeps working.

---

## AI Briefing

### Briefing button is disabled with "Monthly Anthropic budget reached"

You've hit `ANTHROPIC_MONTHLY_BUDGET_USD` (default $5.00). By design, the only way to re-enable before month-end is to manually raise that value in `.env`.

**Fix:**
```
# In .env, edit:
ANTHROPIC_MONTHLY_BUDGET_USD=10.00
```
Then restart the dashboard. The meter shows the new cap immediately.

### Button shows "Wait N minutes" — how do I override?

Rate limit: default 1 briefing per hour. Set by `ANTHROPIC_MIN_MINUTES_BETWEEN_BRIEFINGS` in `.env`. To lower it:
```
ANTHROPIC_MIN_MINUTES_BETWEEN_BRIEFINGS=15
```
Restart the dashboard.

### Got a 429 error when generating

Anthropic rate-limited the request. Per PRD §5.6 #8, the app does not retry automatically. Wait a few minutes and try again.

### Briefing generated but the cache file has weird YAML at the top

That's intentional — YAML frontmatter with provenance (timestamp, model, tokens, cost). If you open `briefings/2026-04-22.md` in a plain text editor, you'll see it. When you download via the dashboard button, it's included for your records. The dashboard itself strips it before rendering.

### I want to clear my usage ledger

The ledger is at `briefings/.usage.jsonl`. Deleting the file resets your monthly spend to $0 — but **this is self-defeating**: the cap exists to stop you from going over by accident. Raising the cap in `.env` is almost always the right move instead.

If you really want to clear it (e.g. corrupt file):
```bash
# macOS:
rm briefings/.usage.jsonl

# Windows:
del briefings\.usage.jsonl
```

---

## Adding / editing tickers

### Added a ticker to `tickers.yaml`, dashboard still shows the old list

Streamlit caches `Settings` per process. Click the sidebar **Refresh** button, or restart the dashboard.

### Ticker symbol not recognized by yfinance

Some foreign tickers need a suffix: `TSLA` (US) works, but `SHOP.TO` (Shopify on TSX), `VOD.L` (Vodafone on LSE), `005930.KS` (Samsung on KOSPI) need exchange suffixes. yfinance uses Yahoo's symbol conventions.

### How do I reset to the original 5-ticker list?

```bash
git checkout config/tickers.yaml
# If not a git repo or no changes checked in yet, manually restore to:
# CRDO, HIMS, BABA, QQQI, IREN (see config/tickers.yaml in the upstream repo)
```

---

## macOS specifics

### Gatekeeper blocked a script

Python scripts aren't subject to Gatekeeper. If you see a blocked-app dialog, you probably double-clicked something else — not a `run.py` issue.

### `command not found: brew`

Homebrew isn't installed. Install it:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
After the install completes, restart Terminal so `brew` appears on PATH. Apple Silicon (M1/M2/M3) installs Homebrew at `/opt/homebrew` by default.

### Xcode command-line tools prompt on first `git` use

Expected. Click **Install**. ~5 min download. Git + most dev tools depend on these. If you've dismissed the prompt by accident, re-trigger with `xcode-select --install`.

### VS Code `code` command not on PATH

Open VS Code → Command Palette (Cmd+Shift+P) → type "Shell Command: Install 'code' command in PATH" → Enter. Restart Terminal.

### Terminal shows "zsh: command not found" for python3

Your shell doesn't see the new Python install. Either:
- Restart Terminal (most common fix — PATH hasn't reloaded)
- Or explicitly reload: `source ~/.zshrc`
- Or invoke directly: `/opt/homebrew/bin/python3.11 run.py setup`

---

## Windows specifics

### The `🔄 Refresh data` button does nothing

Very rare. Usually the click registers but the cache wasn't cleared. Stop and restart:
```powershell
python run.py stop && python run.py start
```

### `Microsoft Defender SmartScreen` blocked a script

Allow the script through. The warning is for unsigned binaries, which `run.py` isn't — but Windows can occasionally flag `streamlit run` scripts during first launch.

### Terminal output shows garbled characters

`setup_check.py` and `run.py` force UTF-8 stdout explicitly, but if you're running a non-project script in an older cmd.exe, set:
```powershell
chcp 65001
```
before running to switch the codepage to UTF-8.

---

## When none of the above helps

1. Run `python3 run.py setup` (or `python run.py setup` on Windows) — it validates the environment and reports what's off.
2. Check the Streamlit log — run in foreground:
   - macOS: `./.venv/bin/python -m streamlit run app.py`
   - Windows: `.\.venv\Scripts\python.exe -m streamlit run app.py`
3. Post the exact error message (no screenshots) to your agent. Include the last 10 lines of the stack trace.

The agent should:
- Read the traceback top-to-bottom
- Identify the file + line number
- Fix the root cause, not the symptom
- Re-run tests: `python3 run.py test` (or `python run.py test` on Windows)
