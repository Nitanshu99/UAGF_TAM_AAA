"""Serving the snapshot page and capturing it, whole."""
from __future__ import annotations

import http.client
import os
import pathlib
import subprocess
import sys
import time

from scripts.wizard_fill.session import shoot

_PAGE = pathlib.Path(__file__).with_name("page.py")
#: A heading every results dashboard renders, whatever the verdict.
_RENDERED = "Your documents"


def serve(state: pathlib.Path, port: int) -> subprocess.Popen:
    """Start Streamlit on *port* with the page over *state*; returns once it answers."""
    env = {**os.environ, "AAA_SNAPSHOT_STATE": str(state.resolve())}
    # The server outlives this call; the caller terminates it (no `with`).
    proc = subprocess.Popen(  # noqa: S603  # pylint: disable=consider-using-with
        [sys.executable, "-m", "streamlit", "run", str(_PAGE), "--server.port", str(port),
         "--server.headless", "true", "--browser.gatherUsageStats", "false"],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        # A plain HTTP connection to localhost: no URL, so no scheme to get wrong.
        connection = http.client.HTTPConnection("localhost", port, timeout=2)
        try:
            connection.request("GET", "/_stcore/health")
            if connection.getresponse().status == 200:
                return proc
        except OSError:
            time.sleep(1)
        finally:
            connection.close()
    proc.terminate()
    raise RuntimeError(f"streamlit did not answer on port {port}")


def capture(url: str, target: pathlib.Path) -> None:
    """Open *url* headless, wait for the dashboard, and save a full-page screenshot."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.goto(url, wait_until="networkidle")
        page.get_by_text(_RENDERED).first.wait_for(timeout=120_000)
        page.wait_for_timeout(3000)  # charts and cards finish drawing
        shoot(page, target)
        browser.close()


__all__ = ["capture", "serve"]
