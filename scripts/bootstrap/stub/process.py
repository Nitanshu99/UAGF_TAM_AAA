"""Run the stub as a child of the bootstrap and point the stack at it."""
from __future__ import annotations

import socket
import subprocess
from pathlib import Path

from scripts.bootstrap.paths import LOG_DIR, REPO_ROOT
from scripts.bootstrap.steps.app import wait_http

#: The stub's usual port. Fixed rather than random because the port is part of
#: the corpus identity stamp (``openrouter@127.0.0.1:8765``): a stable address
#: lets one mock run reuse the corpus the previous one embedded.
STUB_PORT = 8765


def free_port(preferred: int = STUB_PORT) -> int:
    """*preferred* when it is free, else a loopback port nothing is listening on."""
    with socket.socket() as sock:
        try:
            sock.bind(("127.0.0.1", preferred))
            return preferred
        except OSError:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])


def start_stub(python: Path) -> tuple[subprocess.Popen, str]:
    """Start the stub and wait for it.

    :param python: The venv interpreter.
    :returns: The process and the ``OPENROUTER_API_BASE`` that reaches it.
    """
    port = free_port()
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log = (LOG_DIR / "stub.log").open("ab")
    proc = subprocess.Popen(  # pylint: disable=consider-using-with
        [str(python), "-m", "scripts.bootstrap.stub", "--port", str(port)],
        cwd=REPO_ROOT, stdout=log, stderr=subprocess.STDOUT)
    wait_http(f"http://127.0.0.1:{port}/health", proc, timeout=30)
    return proc, f"http://127.0.0.1:{port}/api/v1"
