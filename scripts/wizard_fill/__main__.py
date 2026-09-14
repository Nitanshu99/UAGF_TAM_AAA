"""Fill the Mariposa wizard form with Playwright.

    python -m scripts.wizard_fill                   # opens a visible browser
    python -m scripts.wizard_fill --run             # also start the audit
    python -m scripts.wizard_fill --headless        # no window (CI only)

Filling only is free and takes about a minute; ``--run`` dispatches a paid
audit, so it is off by default and the preflight is checked first.
"""
from __future__ import annotations

import pathlib
import sys

from playwright.sync_api import sync_playwright

from scripts.wizard_fill.cli import parse_args, results_path
from scripts.wizard_fill.flow import drive
from scripts.wizard_fill.preflight import CASE_DOC, preflight
from scripts.wizard_fill.session import capture_downloads, hold_open, shoot, watch

# The session helpers moved to ``scripts.wizard_fill.session`` so the bootstrap
# can share them; these names are kept for callers and tests that import them.
_capture_downloads, _watch, _shoot, _hold_open = capture_downloads, watch, shoot, hold_open
_preflight, _results_path = preflight, results_path


def main() -> int:
    """Fill the form, and optionally start the audit."""
    args = parse_args()
    case_dir = pathlib.Path(args.case_dir)

    if args.run and not _preflight(case_dir):
        print("\nrefusing to dispatch: this run is not comparable with the baseline.")
        return 1

    pw = sync_playwright().start()
    # Headed by default. A headless run is invisible: there is no window to
    # watch, nothing to interrupt, and when the driver exits the wizard
    # session that owns the audit has no viewer at all — the work continues
    # server-side with no way to see it.
    # `channel="chromium"` runs the full build rather than the separate
    # headless-shell download, which this machine does not have.
    browser = pw.chromium.launch(headless=args.headless, channel="chromium")
    page = browser.new_page(viewport={"width": 1440, "height": 1100},
                            accept_downloads=True)
    _capture_downloads(page, pathlib.Path(args.downloads))
    interrupted = False
    try:
        code, interrupted = drive(page, args, case_dir)
    finally:
        # After an interrupt the driver loop may be dead and any call would
        # block; exiting the process closes the driver and the browser instead.
        if not interrupted:
            if not args.run:
                browser.close()
            pw.stop()
    return code


__all__ = ["CASE_DOC", "main"]


if __name__ == "__main__":
    sys.exit(main())
