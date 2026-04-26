"""Start the Streamlit dashboard and record its PID.

Usage:
    python scripts/start_dashboard.py

Behavior:
- Checks for an existing .streamlit.pid; if the process is alive, prints
  a message and exits 0 (already running).
- If the PID file is stale, removes it.
- Spawns `streamlit run app.py` as a detached background process on
  Windows / POSIX, writes the PID to .streamlit.pid.
- Prints the local URL so the agent can pass it to the user.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PID_FILE = PROJECT_ROOT / ".streamlit.pid"
APP_FILE = PROJECT_ROOT / "app.py"
DEFAULT_URL = "http://localhost:8501"


def _pid_alive(pid: int) -> bool:
    try:
        if os.name == "nt":
            # Windows — use tasklist
            out = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True,
                text=True,
                check=False,
            )
            return str(pid) in out.stdout
        # POSIX — signal 0 checks existence
        os.kill(pid, 0)
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def main() -> int:
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
        except ValueError:
            pid = -1
        if pid > 0 and _pid_alive(pid):
            print(f"Dashboard already running (PID {pid}). Visit {DEFAULT_URL}.")
            return 0
        print("Found stale PID file — cleaning up.")
        PID_FILE.unlink(missing_ok=True)

    if not APP_FILE.exists():
        print(f"ERROR: {APP_FILE} not found.")
        return 1

    cmd = [sys.executable, "-m", "streamlit", "run", str(APP_FILE)]

    if os.name == "nt":
        # Windows — new process group so we can kill cleanly
        flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
        proc = subprocess.Popen(
            cmd,
            cwd=str(PROJECT_ROOT),
            creationflags=flags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        proc = subprocess.Popen(
            cmd,
            cwd=str(PROJECT_ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

    PID_FILE.write_text(str(proc.pid))
    # Give Streamlit a moment to boot so the URL is actually live.
    time.sleep(2)
    print(f"Dashboard started (PID {proc.pid}). Visit {DEFAULT_URL}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
