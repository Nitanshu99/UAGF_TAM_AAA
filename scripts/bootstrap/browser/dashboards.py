"""Opening every service dashboard in its own tab of the shared browser context."""
from __future__ import annotations

import pathlib
import re
from typing import Any

from scripts.bootstrap.browser.tabs import Tab
from scripts.wizard_fill.session import shoot


def _slug(name: str) -> str:
    """``"Grafana · pipeline overview"`` → ``grafana_pipeline_overview``."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def open_dashboards(context: Any, tabs: list[Tab], shots: pathlib.Path | None,
                    env: dict[str, str] | None = None) -> list[str]:
    """Open every service tab; a tab that fails to load is reported, not fatal.

    :param context: The browser context all tabs share.
    :param tabs: What to open, in order.
    :param shots: Directory for one PNG per tab, or ``None``.
    :param env: Environment for the tabs' ``after`` hooks (sign-in forms).
    :returns: Names of the tabs that did not load.
    """
    failed: list[str] = []
    for index, tab in enumerate(tabs, 1):
        page = context.new_page()
        try:
            page.goto(tab.url, wait_until="domcontentloaded", timeout=30_000)
            page.wait_for_timeout(750)
        except Exception as exc:  # noqa: BLE001 - one dead dashboard must not stop the rest
            failed.append(tab.name)
            print(f"  [{index:2d}] {tab.name:<34} {tab.url}  (not reachable: "
                  f"{type(exc).__name__})", flush=True)
            continue
        note = tab.after(page, env or {}) if tab.after else tab.note
        print(f"  [{index:2d}] {tab.name:<34} {tab.url}", flush=True)
        if note:
            print(f"       {note}", flush=True)
        if shots:
            shoot(page, shots / f"tab_{index:02d}_{_slug(tab.name)}.png")
    return failed


__all__ = ["open_dashboards"]
