"""Argument parsing for the ``aaa`` launcher front door."""
from __future__ import annotations

import argparse


def parse_launcher_args(argv: list[str] | None) -> tuple[argparse.Namespace, list[str]]:
    """Parse launcher arguments, keeping unknown ones for pass-through commands.

    :param argv: Argument vector (defaults to ``sys.argv[1:]``).
    :type argv: list[str] | None
    :returns: Parsed namespace plus pass-through arguments.
    :rtype: tuple[argparse.Namespace, list[str]]
    """
    parser = argparse.ArgumentParser(
        prog="aaa", description="AAA — Autonomous AI Auditor launcher.")
    parser.add_argument(
        "component", nargs="?", default="all",
        choices=["all", "ui", "api", "audit", "report"],
        help="What to start (default: all, as configured in .env).")
    return parser.parse_known_args(argv)
