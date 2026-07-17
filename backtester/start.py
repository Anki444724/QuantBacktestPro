#!/usr/bin/env python3
"""Start the QuantBacktest Pro backend and keep it running."""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
BACKEND = ROOT / "backend"
LOG_FILE = Path("/tmp/quantbacktest.log")
PID_FILE = Path("/tmp/quantbacktest.pid")


def is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def stop_existing():
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            if is_running(pid):
                os.kill(pid, signal.SIGTERM)
                for _ in range(20):
                    if not is_running(pid):
                        break
                    time.sleep(0.2)
                if is_running(pid):
                    os.kill(pid, signal.SIGKILL)
        except Exception:
            pass
    # Also kill any other uvicorn on port 8000
    subprocess.run(
        ["pkill", "-f", "uvicorn main:app --host 0.0.0.0 --port 8000"],
        capture_output=True,
    )


def install_deps():
    print("Installing/updating dependencies...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"],
        cwd=BACKEND,
        check=True,
    )


def start_backend() -> int:
    print("Starting FastAPI backend on http://localhost:8000 ...")
    log = open(LOG_FILE, "a")
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=BACKEND,
        stdout=log,
        stderr=log,
        preexec_fn=os.setsid,
    )
    PID_FILE.write_text(str(process.pid))
    return process.pid


def wait_for_backend(timeout: int = 15) -> bool:
    import urllib.request

    for _ in range(timeout * 2):
        try:
            with urllib.request.urlopen("http://localhost:8000/api/health", timeout=1) as resp:
                data = resp.read().decode()
                if '"status":"ok"' in data:
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def main():
    print("=== QuantBacktest Pro Startup ===")
    stop_existing()
    install_deps()
    pid = start_backend()
    if wait_for_backend():
        print(f"Backend is ONLINE (pid {pid})")
        print("Open: http://localhost:8000/")
        print("API docs: http://localhost:8000/docs")
        print(f"Logs: tail -f {LOG_FILE}")
    else:
        print("Backend failed to start. Check logs:")
        print(LOG_FILE.read_text() if LOG_FILE.exists() else "No log file")
        sys.exit(1)


if __name__ == "__main__":
    main()
