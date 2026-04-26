# HELP — First-aid when something's not working

**When anything feels off — dashboard won't open, prices are blank, AI Briefing button does nothing, news tab is empty — start here.**

Paste the prompt below to your Claude Code agent. It will run through a full diagnostic sweep, tell you exactly what's OK and what's broken, and give you one concrete fix per broken item.

Most of the checks won't be relevant to your specific problem — that's fine. The sweep is cheap and catches things you wouldn't think to look for.

---

## The one prompt

Copy everything inside the box and paste it to your agent:

```
My Equity Research Desk isn't working properly. Please run a full diagnostic
using HELP.md in the project root as your checklist. Walk through every section
in order:

  1. Python + venv + dependencies
  2. .env file hygiene (this is what usually breaks — check for the .env.txt trap)
  3. API key formatting (quotes, whitespace, leading #, sk-ant- prefix)
  4. Dashboard process + port 8501
  5. yfinance live connectivity
  6. Output of `python run.py setup`

For each item report OK / BROKEN / NOT APPLICABLE. For anything broken, give me
the exact one-command fix I should run, or the exact file edit you'll make.
Don't fix anything without showing me the plan first.
```

That's it. Paste, send, wait for the report.

---

## What the agent is checking (and why)

> All command examples below use macOS conventions (`python3`, `ls`, `ps`). If you're on Windows, swap `python3` → `python` (or `py`), `ls` → `dir`, `ps -p PID` → `tasklist /FI "PID eq <pid>"`.

### 1. Python + venv + dependencies

- **`python3 --version`** must return 3.11 or newer. (On Windows: `python --version` or `py --version`.) If it's missing, install via `brew install python@3.11` on macOS, or `winget install -e --id Python.Python.3.11` on Windows.
- **`.venv/` directory** must exist in the project root. If missing: `python3 run.py setup`.
- **Core deps installed**: `streamlit`, `plotly`, `yfinance`, `pandas`, `python-dotenv`, `PyYAML`, `requests`, `anthropic`, `markdown`. If any are missing, `python3 run.py setup` reinstalls them all.

### 2. `.env` file hygiene — this is what usually breaks

**The failure mode that cost us a whole lesson last time was here.** Read this section carefully before accusing the code.

- **File must be named exactly `.env`** — NOT `.env.txt`, NOT `.env.rtf`, NOT `env.txt`, NOT `env.`. Two common traps:
  - **macOS Finder hides known extensions by default.** A file that looks like `.env` in Finder might be `.env.rtf` on disk if it was saved from TextEdit. Verify with `ls -la | grep env` in Terminal — that shows the real name.
  - **Windows File Explorer hides `.txt` by default.** Notepad silently appends `.txt` when saving a file called `.env`.
- **File must be in the project root**, next to `app.py` and `run.py`. Not in a subfolder.
- **Each key on its own line**, exactly like `.env.example`:
  ```
  ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
  FINNHUB_API_KEY=d4xxxxxxxxxxxxxxxxxx
  ```
- **Do NOT wrap values in quotes**. `ANTHROPIC_API_KEY="sk-ant-..."` breaks — `python-dotenv` includes the literal quotes in the value and Anthropic rejects the key.
- **Do NOT put `#` at the start of a key line**. That comments the key out. `# ANTHROPIC_API_KEY=...` → key is never read.
- **Trailing whitespace silently truncates the key**. `sk-ant-... ` (note the trailing space) will fail with a cryptic 401. Check for invisible trailing chars.
- **Anthropic keys start with `sk-ant-`**. If yours doesn't, you pasted something else (an OpenAI key, a placeholder, the login password).
- **Finnhub keys are lowercase alphanumeric, ~20 chars**, no prefix.
- **Don't edit `.env` in TextEdit on Mac.** TextEdit defaults to rich-text format. Use VS Code (`code .env`) or `nano .env` in Terminal — or better, have the agent edit it directly via its file tools.
- **After editing `.env`, the dashboard MUST be restarted** — `.env` is read once at startup. Hitting Refresh in the sidebar does NOT re-read `.env`. Run `python3 run.py stop && python3 run.py start`.

### 3. Dashboard process + port 8501

- **Is the process alive?** Check for `.streamlit.pid` in the project root. If present, read the PID and verify it's running:
  - macOS/Linux: `ps -p <pid>` — exit 0 if alive, non-zero if dead. Also `kill -0 <pid>` (no actual kill, just tests).
  - Windows: `tasklist /FI "PID eq <pid>"`.
- **Is port 8501 reachable?** Open http://localhost:8501 in the browser (macOS: `open http://localhost:8501`). If "site can't be reached", the dashboard isn't running.
- **Port conflict?** If starting the dashboard errors with "port already in use", a previous instance didn't shut down cleanly. Fix: `python3 run.py stop` then `python3 run.py start`. If stop fails, find + kill the stale python process manually:
  - macOS: `lsof -i :8501` to find the PID, then `kill -9 <pid>`.
  - Windows: `netstat -ano | findstr :8501`, then `taskkill /PID <pid> /F`.

### 4. yfinance live connectivity

- **Live smoke test**: `python3 setup_check.py` step 4 hits yfinance for AAPL and reports OK or FAIL.
- **Rate limits**: yfinance occasionally rate-limits bursts of requests. If prices show as `—` across the whole watchlist, wait 60 seconds and click Refresh.
- **Corporate network / VPN**: some networks block the Yahoo endpoint. If she's on a corporate VPN (common for corporate users), try toggling it off and retry.

### 5. `python3 run.py setup` output

This command runs the full `setup_check.py` validation in six steps. The agent should paste the complete output into the report. Any step that logs `[FAIL]` or `[WARN]` points straight at the problem.

---

## Symptom → most likely cause → fix (quick reference)

| Symptom | Most likely cause | Fix (macOS — swap `python3` → `python` on Windows) |
|---|---|---|
| Dashboard won't start | Venv missing OR port conflict | `python3 run.py setup`, then `python3 run.py start` |
| All prices show `—` | yfinance rate-limited or offline | Wait 60s, click Refresh |
| AI Briefing tab says "no key" despite adding one | `.env` was saved as `.env.rtf` (Mac) or `.env.txt` (Windows) | Rename file; restart dashboard |
| AI Briefing tab says "no key" and file is correctly named | Dashboard wasn't restarted after key added | `python3 run.py stop && python3 run.py start` |
| "Port 8501 already in use" when starting | Previous dashboard instance still running | `python3 run.py stop` first — or find the PID with `lsof -i :8501` (Mac) / `netstat -ano \| findstr :8501` (Windows) and kill manually |
| News tab says "No recent articles" | No Finnhub key, or Finnhub rate limit hit | Check `.env`; free tier is 60 req/min |
| Earnings tab empty | Same as news — needs Finnhub key | Add `FINNHUB_API_KEY` to `.env` |
| "Anthropic call failed: 401" | Key is wrong format (quoted, trailing space, or not `sk-ant-`) | Re-check `.env` formatting rules above |
| "Anthropic call failed: 429" | Rate-limited | Wait 5-10 minutes; the app won't auto-retry |
| AI Brief button disabled, budget shows $X / $Y | Monthly cap hit | Either wait until 1st of next month, OR ask agent to raise `ANTHROPIC_MONTHLY_BUDGET_USD` in `.env` |
| Sidebar says "NYSE Closed" but it's a weekday afternoon | Your machine clock is in a different timezone | Market session is read from system time. On Mac: System Settings → General → Date & Time. |
| `python3: command not found` on Mac | Python isn't installed | `brew install python@3.11` (or python.org installer) |
| `python: command not found` on Windows | Python isn't installed | `winget install -e --id Python.Python.3.11` |

---

## What a healthy system looks like

- **Sidebar**: Title "FX Research Desk", NYSE status pill with a colored dot (green = open, amber = pre/after, red = closed), 5 watchlist cards each with ticker + price + colored % change, "Data sources" section with a green dot next to Yahoo Finance.
- **Overview tab**: Markets row (S&P 500 + Nasdaq-100 benchmarks), watchlist table with 5 rows — each row has a real price, a 30-day sparkline trend, a 52W position bar, and a Day% that's not `—`.
- **No error banners** at the top of any tab.

If all of that is true, the tool is healthy — whatever problem you think you have might be a feature misunderstanding rather than a bug. Ask the agent to explain.

---

## Still broken after the diagnostic?

1. **Paste the full output of `python3 run.py setup`** (on Windows: `python run.py setup`) to your agent and ask it to interpret. The six-step report pinpoints 90% of setup issues.
2. **Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)** — the deeper catalogue of failure modes with specific recipes.
3. **Nuclear option**: ask the agent to delete `.venv/` and re-run `python3 run.py setup` from scratch. This forces a clean dependency reinstall and catches corruption from interrupted installs.
4. **Last resort**: message Sean. Include the full diagnostic report the agent produced + a screenshot of whatever isn't working.
