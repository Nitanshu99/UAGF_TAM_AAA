"""Driving the wizard tab: fill from the bundle, dispatch, wait for the results."""
from __future__ import annotations

import pathlib
from typing import Any

from scripts.wizard_fill import form_spec as spec
from scripts.wizard_fill.mariposa import fill
from scripts.wizard_fill.session import shoot, watch
from scripts.wizard_fill.verify import report_state, verify_labels
from scripts.wizard_fill.widgets import click_button, settle


class BootstrapBrowserError(RuntimeError):
    """Raised when the wizard cannot be driven from the current source."""


def drive_wizard(page: Any, url: str, case_dir: pathlib.Path, *, run: bool,
                 watch_minutes: int, shots: pathlib.Path | None) -> bool:
    """Fill the wizard from the bundle and, when asked, dispatch the audit.

    :param page: The wizard's tab.
    :param url: Where the wizard is served.
    :param case_dir: The intake bundle.
    :param run: Click *Confirm & run* after filling.
    :param watch_minutes: How long to wait for the results dashboard.
    :param shots: Directory for the form / results PNGs, or ``None``.
    :returns: ``True`` when the results dashboard rendered.
    :raises BootstrapBrowserError: When the driver's labels no longer match the UI.
    """
    missing = verify_labels()
    if missing:
        raise BootstrapBrowserError("form spec is out of date with the UI source:\n  - "
                                    + "\n  - ".join(missing))
    unresolved = fill(page, url, case_dir)
    if unresolved:
        print(f"  documents not attached: {unresolved}", flush=True)
    print(report_state(page), flush=True)
    if shots:
        shoot(page, shots / "wizard_filled.png")
    if not run:
        return False
    click_button(page, spec.BUTTONS["run"])
    settle(page, 3000)
    print("  audit dispatched — watch it in the front tab; the other tabs are live.",
          flush=True)
    done = watch(page, watch_minutes)
    if shots:
        shoot(page, shots / "wizard_results.png")
    return done


def drive_or_report(page: Any, url: str, case_dir: pathlib.Path, args: Any) -> None:
    """Drive the wizard; in a headed session, report a failure instead of raising.

    The browser observes the audit. An exception unwinding from here reaches the
    bootstrap's clean-up, which stops the API and UI and with them a running
    audit (T-20260913-023). Headless (CI) still fails loudly.

    :param page: The wizard's tab.
    :param url: Where the wizard is served.
    :param case_dir: The intake bundle.
    :param args: Parsed bootstrap options (``headless``, ``no_run``, ...).
    """
    try:
        drive_wizard(page, url, case_dir, run=not args.no_run,
                     watch_minutes=args.watch_minutes, shots=args.screenshots)
    except Exception as exc:  # noqa: BLE001 - the browser observes the audit; it must not end it
        if args.headless:
            raise
        print(f"  browser driver failed ({type(exc).__name__}: {exc}); the audit continues "
              "server-side and the window stays open.", flush=True)


__all__ = ["BootstrapBrowserError", "drive_or_report", "drive_wizard"]
