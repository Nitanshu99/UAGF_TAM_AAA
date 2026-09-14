"""Application process management for the launcher.

The FastAPI backend runs as a child process; the Streamlit UI runs in the
foreground so that ``Ctrl-C`` stops the whole stack cleanly.
"""
from __future__ import annotations

import logging
import subprocess
import sys

from aaa.launcher.services import REPO_ROOT

logger = logging.getLogger(__name__)


def start_api(port: int) -> subprocess.Popen | None:
    """Start the FastAPI backend with uvicorn as a background child process.

    :param port: TCP port for the API server.
    :returns: The child process handle, or ``None`` on failure.
    """
    cmd = [
        sys.executable, "-m", "uvicorn", "aaa.api.main:app",
        "--host", "0.0.0.0", "--port", str(port),
    ]
    try:
        # The server must outlive this function, so it is not a `with` block.
        proc = subprocess.Popen(cmd, cwd=REPO_ROOT)  # pylint: disable=consider-using-with
    except OSError as exc:
        logger.error("Could not start FastAPI backend: %s", exc)
        return None
    logger.info("FastAPI backend starting on http://localhost:%d", port)
    return proc


def run_ui(port: int) -> int:
    """Run the Streamlit UI in the foreground until interrupted.

    :param port: TCP port for the Streamlit server.
    :returns: The Streamlit process exit code.
    """
    cmd = [
        sys.executable, "-m", "streamlit", "run", "aaa/ui/app.py",
        "--server.port", str(port),
    ]
    logger.info("Streamlit UI starting on http://localhost:%d", port)
    return subprocess.call(cmd, cwd=REPO_ROOT)


def stop(proc: subprocess.Popen | None) -> None:
    """Terminate a child process, escalating to kill after five seconds.

    :param proc: Process returned by :func:`start_api`; ``None`` is a no-op.
    """
    if proc is None or proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
