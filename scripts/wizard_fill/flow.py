"""The fill itself: verify the labels, fill, report, and optionally dispatch the audit."""
from __future__ import annotations

import argparse
import pathlib

from playwright.sync_api import Page

from scripts.wizard_fill.cli import results_path
from scripts.wizard_fill.mariposa import fill
from scripts.wizard_fill.session import hold_open, shoot, watch
from scripts.wizard_fill.verify import report_state, verify_labels
from scripts.wizard_fill.widgets import click_button, settle


def drive(page: Page, args: argparse.Namespace, case_dir: pathlib.Path) -> tuple[int, bool]:
    """Fill the form on *page* and, with ``--run``, start the audit and wait.

    :param page: The wizard's tab.
    :param args: The parsed command line.
    :param case_dir: The intake bundle.
    :returns: ``(exit code, interrupted)`` — *interrupted* is ``True`` when the
        parked browser was closed with Ctrl-C, after which no Playwright call is safe.
    """
    missing = verify_labels()
    if missing:
        print("form spec is out of date with the UI source:")
        for line in missing:
            print(f"  - {line}")
        return 2, False
    unresolved = fill(page, args.url, case_dir)
    if unresolved:
        print(f"  documents not attached: {unresolved}")
    print(report_state(page))
    if args.shot:
        shoot(page, pathlib.Path(args.shot))
    if not args.run:
        return 0, False
    click_button(page, "Confirm & run my audit")
    settle(page, 3000)
    print("  audit dispatched — the browser stays open so the run "
          "can be watched and the dashboard used afterwards.")
    if watch(page) and args.shot:
        shoot(page, results_path(args.shot))
    return 0, hold_open(page)


__all__ = ["drive"]
