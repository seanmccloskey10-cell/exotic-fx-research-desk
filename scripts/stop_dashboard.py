"""Stop the Streamlit dashboard by reading .streamlit.pid.

Usage:
    python scripts/stop_dashboard.py

Behavior:
- Reads .streamlit.pid.
- On Windows: `taskkill /PID <pid> /F /T` (/T also kills child processes).
- On POSIX: os.kill with SIGTERM, then SIGKILL if still alive.
- Removes the PID file.
- Idempotent: exits 0 if no PID file or process already dead.
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


def _pid_alive(pid: int) -> bool:
    try:
        if os.name == "nt":
            out = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True,
                text=True,
                check=False,
            )
            return str(pid) in out.stdout
        os.kill(pid, 0)
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def main() -> int:
    if not PID_FILE.exists():
        print("Dashboard is not running (no .streamlit.pid found).")
        return 0

    try:
        pid = int(PID_FILE.read_text().strip())
    except ValueError:
        print("PID file is corrupted — removing.")
        PID_FILE.unlink(missing_ok=True)
        return 0

    if not _pid_alive(pid):
        print(f"Process {pid} already dead — cleaning up PID file.")
        PID_FILE.unlink(missing_ok=True)
        return 0

    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/F", "/T"],
            capture_output=True,
            check=False,
        )
    else:
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(1)
            if _pid_alive(pid):
                os.kill(pid, signal.SIGKILL)
        except OSError:
            pass

    PID_FILE.unlink(missing_ok=True)
    print(f"Dashboard stopped (PID {pid}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
