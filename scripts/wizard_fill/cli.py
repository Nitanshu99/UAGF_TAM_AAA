"""The ``scripts.wizard_fill`` command line."""
from __future__ import annotations

import argparse
import pathlib

from scripts.wizard_fill.mariposa import CASE_DIR


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the driver's options.

    :param argv: Argument vector (defaults to ``sys.argv[1:]``).
    :returns: The parsed options.
    """
    parser = argparse.ArgumentParser(prog="scripts.wizard_fill")
    parser.add_argument("--url", default="http://localhost:8502")
    parser.add_argument("--case-dir", default=str(CASE_DIR))
    parser.add_argument("--headless", action="store_true",
                        help="hide the browser (default is to show it, so a run "
                             "can be watched and interrupted)")
    parser.add_argument("--run", action="store_true",
                        help="click Confirm & run (dispatches a PAID audit)")
    parser.add_argument("--shot", default=None,
                        help="save a full-page screenshot of the filled form; "
                             "with --run the results dashboard is captured too, "
                             "as <name>_results.png")
    parser.add_argument("--downloads", default="downloads",
                        help="where the dashboard's download buttons save to")
    return parser.parse_args(argv)


def results_path(shot: str) -> pathlib.Path:
    """`x.png` -> `x_results.png`, so the form shot is not overwritten.

    :param shot: The ``--shot`` path.
    :returns: The sibling path for the results screenshot.
    """
    path = pathlib.Path(shot)
    return path.with_name(f"{path.stem}_results{path.suffix or '.png'}")


__all__ = ["parse_args", "results_path"]
