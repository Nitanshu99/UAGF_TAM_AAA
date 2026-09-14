"""Step 9: the FastAPI backend and the Streamlit wizard, as child processes."""
from __future__ import annotations

import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from scripts.bootstrap.paths import LOG_DIR, REPO_ROOT


def _spawn(name: str, cmd: list[str]) -> subprocess.Popen:
    """Start *cmd* with its output in ``logs/bootstrap/<name>.log``."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log = (LOG_DIR / f"{name}.log").open("ab")
    # Outlives this function by design; `stop` ends it.
    return subprocess.Popen(cmd, cwd=REPO_ROOT, stdout=log, stderr=subprocess.STDOUT)  # pylint: disable=consider-using-with


def start_api(python: Path, port: int) -> subprocess.Popen:
    """Start uvicorn on *port*."""
    # All interfaces, deliberately: Prometheus runs in Docker and scrapes this
    # process at `host.docker.internal`, which on Linux resolves through
    # `host-gateway` to the bridge address — a loopback-only bind is unreachable
    # from there and the LLM panels in Grafana go empty. Same as the manual
    # launcher, `aaa.launcher.procs.start_api`.
    return _spawn("api", [str(python), "-m", "uvicorn", "aaa.api.main:app",
                          "--host", "0.0.0.0", "--port", str(port)])  # nosec B104


def start_ui(python: Path, port: int) -> subprocess.Popen:
    """Start the Streamlit wizard on *port*, without opening a browser itself."""
    return _spawn("ui", [str(python), "-m", "streamlit", "run", "aaa/ui/app.py",
                         "--server.port", str(port), "--server.headless", "true",
                         "--browser.gatherUsageStats", "false"])


def wait_http(url: str, proc: subprocess.Popen | None = None, timeout: int = 180) -> None:
    """Poll *url* until it answers 2xx, or *proc* dies, or *timeout* passes.

    :raises ValueError: When *url* is not http or https.
    :raises RuntimeError: When the service never answered.
    """
    # urlopen also opens `file://` and custom schemes; only a web health check
    # is meant here, so refuse anything else before it reaches the opener.
    if urllib.parse.urlsplit(url).scheme not in {"http", "https"}:
        raise ValueError(f"not an http(s) URL: {url!r}")
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc is not None and proc.poll() is not None:
            raise RuntimeError(f"process exited with {proc.returncode} before {url} answered "
                               f"(see {LOG_DIR})")
        try:
            with urllib.request.urlopen(url, timeout=3) as resp:  # noqa: S310  # nosec B310 - scheme checked above
                if 200 <= resp.status < 300:
                    return
        except (urllib.error.URLError, OSError, ValueError):
            pass
        time.sleep(1)
    raise RuntimeError(f"{url} did not answer within {timeout}s (see {LOG_DIR})")


def stop(proc: subprocess.Popen | None) -> None:
    """Terminate a child, escalating to kill after five seconds."""
    if proc is None or proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    if proc.stdout is not None:
        proc.stdout.close()
    sys.stdout.flush()
