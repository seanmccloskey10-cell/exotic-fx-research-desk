"""First-run environment validator + monthly-spend reporter.

Run this BEFORE the first `streamlit run`. the user's agent invokes it as part
of the setup flow (see README.md). It verifies the environment is sane and
tells the agent what to do next.

Checks:
1. Python version >= 3.11
2. Required packages installed
3. `.env` file exists AND is not the Windows `.env.txt` trap
4. yfinance live smoke test (one ticker fetch)
5. Optional API keys validated (if present)
6. Anthropic monthly spend summary (if ANTHROPIC_API_KEY is set)

Exit code 0 means "ready to run". Non-zero means the agent should address
the reported issues.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

# Windows default cp1252 stdout chokes on Unicode. Force UTF-8 with replace
# so this script runs cleanly in cmd.exe, PowerShell, and VS Code terminals.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

PROJECT_ROOT = Path(__file__).resolve().parent
ENV_PATH = PROJECT_ROOT / ".env"
ENV_TXT_TRAP = PROJECT_ROOT / ".env.txt"
USAGE_LOG = PROJECT_ROOT / "briefings" / ".usage.jsonl"

REQUIRED_PACKAGES = [
    "streamlit",
    "yfinance",
    "plotly",
    "pandas",
    "dotenv",       # imported as `dotenv`
    "yaml",         # imported as `yaml` from PyYAML
    "requests",
    "anthropic",
]

MIN_PYTHON = (3, 11)


def _ok(msg: str) -> None:
    print(f"  [OK]   {msg}")


def _warn(msg: str) -> None:
    print(f"  [WARN] {msg}")


def _fail(msg: str) -> None:
    print(f"  [FAIL] {msg}")


def check_python() -> bool:
    print("\n[1/6] Python version")
    v = sys.version_info
    if (v.major, v.minor) >= MIN_PYTHON:
        _ok(f"Python {v.major}.{v.minor}.{v.micro} (>= {MIN_PYTHON[0]}.{MIN_PYTHON[1]})")
        return True
    _fail(
        f"Python {v.major}.{v.minor}.{v.micro} is too old. "
        f"This project requires Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+."
    )
    return False


def check_packages() -> bool:
    print("\n[2/6] Required packages")
    import importlib

    all_good = True
    for pkg in REQUIRED_PACKAGES:
        try:
            importlib.import_module(pkg)
            _ok(f"{pkg}")
        except ImportError:
            _fail(f"{pkg} not installed")
            all_good = False
    if not all_good:
        _fail("Run: pip install -r requirements.txt")
    return all_good


def check_env_file() -> bool:
    print("\n[3/6] .env file")
    if ENV_TXT_TRAP.exists():
        _fail(
            ".env.txt exists! Windows hid the .txt extension and created the "
            "wrong file. Rename `.env.txt` to `.env` (exactly, no extension). "
            "See README for the Windows hidden-extension fix."
        )
        return False
    if not ENV_PATH.exists():
        _warn(
            ".env file not found. The dashboard will still run on yfinance "
            "(no key needed), but optional features require keys. Ask your "
            "agent: \"Copy .env.example to .env for me.\""
        )
        return True  # not a failure — yfinance works without it
    _ok(".env exists")
    return True


def check_yfinance() -> bool:
    print("\n[4/6] yfinance live smoke test")
    try:
        import yfinance as yf

        # Use EURUSD=X for the smoke test — it's the canonical default in
        # this FX variant's watchlist and exercises yfinance's FX path
        # (which is what the dashboard will actually use).
        t = yf.Ticker("EURUSD=X")
        hist = t.history(period="5d")
        if len(hist) > 0 and "Close" in hist.columns:
            price = hist["Close"].iloc[-1]
            _ok(f"yfinance returned live data for EURUSD=X (last close: {price:.6f})")
            return True
        _warn(
            "yfinance returned no price for EURUSD=X. Could be a transient network "
            "issue or Yahoo Finance rate-limiting. Try again in a minute."
        )
        return True
    except Exception as e:
        _fail(f"yfinance smoke test failed: {e}")
        return False


def check_optional_keys() -> None:
    print("\n[5/6] Optional API keys")
    try:
        from config.settings import load_settings

        s = load_settings()
    except Exception as e:
        _fail(f"Could not load settings: {e}")
        return

    items = [
        ("FINNHUB_API_KEY", s.has_finnhub, "news + earnings calendar"),
        ("ALPHAVANTAGE_API_KEY", s.has_alphavantage, "backup fundamentals"),
        ("ANTHROPIC_API_KEY", s.has_anthropic, "AI briefings"),
    ]
    for name, present, unlocks in items:
        if present:
            _ok(f"{name} detected — unlocks {unlocks}")
        else:
            _warn(f"{name} not set — {unlocks} disabled (optional)")


def check_anthropic_spend() -> None:
    """Per PRD §5.6 #10 — show current monthly spend if key is set."""
    print("\n[6/6] Anthropic monthly spend")
    try:
        from config.settings import load_settings

        s = load_settings()
    except Exception:
        _warn("Could not load settings; skipping spend check.")
        return

    if not s.has_anthropic:
        _ok("ANTHROPIC_API_KEY not set — nothing to report.")
        return

    cap = s.anthropic_monthly_budget_usd
    if not USAGE_LOG.exists():
        _ok(f"Anthropic spend this month: $0.00 / ${cap:.2f}")
        return

    now = datetime.now()
    total = 0.0
    try:
        with USAGE_LOG.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                ts = entry.get("timestamp")
                if not ts:
                    continue
                dt = datetime.fromisoformat(ts)
                if dt.year == now.year and dt.month == now.month:
                    total += float(entry.get("cost_usd", 0.0))
    except Exception as e:
        _warn(f"Could not parse usage log: {e}")
        return

    pct = (total / cap * 100.0) if cap > 0 else 0.0
    if total >= cap:
        _fail(
            f"Anthropic spend this month: ${total:.2f} / ${cap:.2f} ({pct:.1f}%). "
            f"Monthly cap reached — briefing button is disabled until the 1st of "
            f"next month, OR until you raise ANTHROPIC_MONTHLY_BUDGET_USD in .env."
        )
    else:
        _ok(f"Anthropic spend this month: ${total:.2f} / ${cap:.2f} ({pct:.1f}%)")


def main() -> int:
    print("=" * 60)
    print(" FX Research Desk — setup check")
    print("=" * 60)

    ok = True
    ok &= check_python()
    ok &= check_packages()
    ok &= check_env_file()
    if ok:
        ok &= check_yfinance()
        check_optional_keys()
        check_anthropic_spend()

    print("\n" + "=" * 60)
    if ok:
        print(" [OK] Ready to run.")
        print("      Next step -- say to your agent: \"Start the dashboard.\"")
        print("=" * 60)
        return 0
    print(" [FAIL] Setup issues found. Fix the items above, then re-run:")
    print("        python run.py setup")
    print("=" * 60)
    return 1


if __name__ == "__main__":
    sys.exit(main())
