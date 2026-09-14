"""Step 10: one Chromium window — every dashboard in a tab, the wizard in front."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from scripts.bootstrap.browser.dashboards import open_dashboards
from scripts.bootstrap.browser.login import sign_in_grafana, sign_in_minio
from scripts.bootstrap.browser.session import drive_or_report
from scripts.bootstrap.browser.tabs import service_tabs
from scripts.bootstrap.environment import port
from scripts.wizard_fill.session import capture_downloads, hold_open


def pre_sign_in(context: Any, env: dict[str, str]) -> None:
    """Log the shared cookie jar into MinIO and Grafana before any tab opens."""
    minio = f"http://localhost:{port(env, 'MINIO_CONSOLE_PORT', 9001)}"
    grafana = f"http://localhost:{port(env, 'GRAFANA_PORT', 3002)}"
    results = {
        "MinIO console": sign_in_minio(context, minio, env.get("MINIO_ROOT_USER") or "",
                                       env.get("MINIO_ROOT_PASSWORD") or ""),
        "Grafana (admin)": sign_in_grafana(context, grafana,
                                           env.get("GF_SECURITY_ADMIN_PASSWORD") or "admin"),
    }
    for name, done in results.items():
        print(f"  {'signed in' if done else 'NOT signed in'}: {name}", flush=True)


def browse(args: argparse.Namespace, env: dict[str, str], ui_url: str, case_dir: Path) -> None:
    """Open the tabs, fill and run the wizard, and hold the window open.

    Every page comes from one browser context, which is what makes them tabs of
    the same window rather than separate windows; the wizard is opened last and
    brought to the front so the run is what the operator is looking at.

    :param args: Parsed bootstrap options.
    :param env: The environment the stack was started with (for ports).
    :param ui_url: Where the wizard is served.
    :param case_dir: The intake bundle to fill from.
    """
    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    interrupted = False
    try:
        # `channel="chromium"` is the full build `playwright install chromium`
        # fetches, headed or not.
        browser = pw.chromium.launch(headless=args.headless, channel="chromium")
        context = browser.new_context(viewport={"width": 1440, "height": 1000},
                                      accept_downloads=True)
        pre_sign_in(context, env)
        open_dashboards(context, service_tabs(env), args.screenshots, env)
        page = context.new_page()
        capture_downloads(page, args.downloads)
        page.bring_to_front()
        drive_or_report(page, ui_url, case_dir, args)
        if not args.headless:
            interrupted = hold_open(page, stop_hint="pkill -f scripts.bootstrap")
    finally:
        # After an interrupt the driver loop may be dead and any call would
        # block; exiting the process closes the driver and the browser instead.
        if not interrupted:
            _quit(pw)


def _quit(pw: Any) -> None:
    """Stop the Playwright driver (and the browser with it), tolerating a gone window."""
    try:
        pw.stop()
    except Exception:  # noqa: BLE001 - already gone when the window was closed by hand
        pass
