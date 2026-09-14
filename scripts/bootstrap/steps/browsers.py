"""Step 7: the Chromium build Playwright drives."""
from __future__ import annotations

import platform
from pathlib import Path

from scripts.setup.console import ok, warn
from scripts.setup.shell import run


def install_chromium(python: Path) -> None:
    """``playwright install chromium`` — a no-op once the build is cached.

    :param python: The venv interpreter (Playwright lives there).
    """
    code = run([str(python), "-m", "playwright", "install", "chromium"], check=False)
    if code != 0:
        warn("playwright install chromium failed; the browser step will not work")
        return
    if platform.system() == "Linux":
        warn("on Linux the browser may also need system libraries: "
             "`sudo .venv/bin/python -m playwright install-deps chromium`")
    ok("chromium ready")
