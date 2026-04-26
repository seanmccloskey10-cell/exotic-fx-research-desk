"""One-command wrapper — handles venv creation, dependency install, and dispatch.

Usage:
    python run.py setup     # Create venv, install deps, validate environment
    python run.py start     # Start the dashboard (http://localhost:8501)
    python run.py stop      # Stop the dashboard
    python run.py test      # Run the pytest suite
    python run.py shell     # Print the venv python path (for agent use)

This is the ONE command Roula's agent should use after git clone. It hides:
- Virtual environment creation (`python -m venv .venv`)
- Dependency installation (`pip install -r requirements.txt`)
- Cross-platform venv Python path (`.venv/Scripts/python.exe` vs `.venv/bin/python`)
- Re-install detection (if requirements.txt changes, deps are reinstalled)

The only prerequisite is Python 3.11+ on the system. See README.md "Preflight
checks" for how the agent installs Python and Git if they are missing.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# Force UTF-8 stdout on Windows so non-ASCII characters don't explode in cmd.exe.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
REQUIREMENTS = ROOT / "requirements.txt"
DEPS_MARKER = VENV / ".deps_installed"
ENV_FILE = ROOT / ".env"
ENV_EXAMPLE = ROOT / ".env.example"
MIN_PY = (3, 11)


def _check_python_version() -> None:
    v = sys.version_info
    if (v.major, v.minor) < MIN_PY:
        print(
            f"ERROR: Python {v.major}.{v.minor}.{v.micro} is too old. "
            f"Need Python {MIN_PY[0]}.{MIN_PY[1]}+.\n"
            "  macOS:   brew install python@3.11   (or download from https://www.python.org/downloads/)\n"
            "  Windows: winget install -e --id Python.Python.3.11\n"
            "  Any OS:  https://www.python.org/downloads/"
        )
        sys.exit(1)


def venv_python() -> Path:
    """Return the path to the venv's Python interpreter."""
    if os.name == "nt":
        return VENV / "Scripts" / "python.exe"
    return VENV / "bin" / "python"


def ensure_venv() -> None:
    if venv_python().exists():
        return
    print(f"Creating virtual environment at {VENV.relative_to(ROOT)}/ ...")
    subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True)
    if not venv_python().exists():
        print("ERROR: venv creation appeared to succeed but Python was not found.")
        print(f"  Expected: {venv_python()}")
        sys.exit(1)


def ensure_deps(force: bool = False) -> None:
    # Re-install when requirements.txt is newer than the last install marker.
    if not force and DEPS_MARKER.exists():
        if REQUIREMENTS.stat().st_mtime <= DEPS_MARKER.stat().st_mtime:
            return
    print("Installing dependencies (this takes ~1 minute on first run) ...")
    subprocess.run(
        [str(venv_python()), "-m", "pip", "install", "--upgrade", "pip"],
        check=True,
        cwd=str(ROOT),
    )
    subprocess.run(
        [str(venv_python()), "-m", "pip", "install", "-r", str(REQUIREMENTS)],
        check=True,
        cwd=str(ROOT),
    )
    DEPS_MARKER.touch()


def run_in_venv(args: list[str]) -> int:
    proc = subprocess.run([str(venv_python()), *args], cwd=str(ROOT))
    return proc.returncode


def ensure_env_file() -> None:
    """Copy .env.example to .env if .env is missing.

    Bypasses Windows' hidden-extension trap (Notepad's "save as .env" tends
    to produce .env.txt) by doing the copy in pure Python.
    """
    if ENV_FILE.exists():
        return
    if not ENV_EXAMPLE.exists():
        print("WARNING: neither .env nor .env.example exists. Skipping.")
        return
    print("Creating .env from .env.example (no keys set -- dashboard runs on yfinance) ...")
    ENV_FILE.write_text(ENV_EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")


def cmd_setup() -> int:
    ensure_venv()
    ensure_deps()
    ensure_env_file()
    return run_in_venv(["setup_check.py"])


def cmd_start() -> int:
    ensure_venv()
    ensure_deps()
    return run_in_venv(["scripts/start_dashboard.py"])


def cmd_stop() -> int:
    # Stop doesn't strictly need deps, but does need the venv Python
    # so the stop script's sys.executable matches the start script's.
    ensure_venv()
    return run_in_venv(["scripts/stop_dashboard.py"])


def cmd_test(extra: list[str]) -> int:
    ensure_venv()
    ensure_deps()
    return run_in_venv(["-m", "pytest", *extra])


def cmd_shell() -> int:
    ensure_venv()
    print(str(venv_python()))
    return 0


COMMANDS = {
    "setup": lambda extra: cmd_setup(),
    "start": lambda extra: cmd_start(),
    "stop": lambda extra: cmd_stop(),
    "test": lambda extra: cmd_test(extra),
    "shell": lambda extra: cmd_shell(),
}


def _usage() -> None:
    print("Usage: python run.py <command>")
    print("Commands:")
    print("  setup   Create venv, install deps, validate environment")
    print("  start   Start the dashboard at http://localhost:8501")
    print("  stop    Stop the dashboard")
    print("  test    Run the pytest suite")
    print("  shell   Print the venv python path")


def main() -> int:
    _check_python_version()
    if len(sys.argv) < 2:
        _usage()
        return 1
    cmd = sys.argv[1]
    extra = sys.argv[2:]
    handler = COMMANDS.get(cmd)
    if not handler:
        print(f"Unknown command: {cmd}\n")
        _usage()
        return 1
    return handler(extra)


if __name__ == "__main__":
    sys.exit(main())
