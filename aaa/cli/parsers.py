"""Sub-parser definitions for the AAA CLI (``run`` and ``report``)."""
from __future__ import annotations

import argparse


def add_run_parser(sub: argparse._SubParsersAction) -> None:
    """Register the ``run`` sub-command on *sub*.

    :param sub: The CLI's sub-parsers action.
    :type sub: argparse._SubParsersAction
    """
    run_p = sub.add_parser("run", help="Run a full audit engagement.")
    run_p.add_argument("--engagement-id", required=True,
                       help="Unique engagement identifier (UUID or slug).")
    run_p.add_argument("--intake-dir", required=True,
                       help="Directory containing stage_a.json / stage_b.json "
                            "[/ stage_c.json] payloads.")
    run_p.add_argument("--cgsa-fixture-dir", default=None,
                       help="Optional CGSA fixture directory "
                            "(sets CGSA_FIXTURE_DIR for the GovernanceAgent).")
    run_p.add_argument("--output-file", default=None,
                       help="Optional path to write the JSON summary.")
    run_p.add_argument("--annex-iv-schema-version", default="1.0.0",
                       help="Annex IV schema version (default: 1.0.0).")
    run_p.add_argument("--log-level", default="WARNING",
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"])


def add_report_parser(sub: argparse._SubParsersAction) -> None:
    """Register the ``report`` sub-command on *sub*.

    :param sub: The CLI's sub-parsers action.
    :type sub: argparse._SubParsersAction
    """
    report_p = sub.add_parser(
        "report", help="Regenerate customer PDF reports from data/customer/.")
    report_group = report_p.add_mutually_exclusive_group(required=True)
    report_group.add_argument("--all", action="store_true",
                              help="Render a PDF for every company folder.")
    report_group.add_argument("--company", default=None,
                              help="Render only this company folder (normalized name).")
    report_p.add_argument("--log-level", default="WARNING",
                          choices=["DEBUG", "INFO", "WARNING", "ERROR"])


def add_brief_parser(sub: argparse._SubParsersAction) -> None:
    """Register the ``brief`` sub-command on *sub*.

    Unlike ``report``, this one calls the model: it writes the plain-language
    client brief from a saved audit state.

    :param sub: The CLI's sub-parsers action.
    :type sub: argparse._SubParsersAction
    """
    brief_p = sub.add_parser(
        "brief", help="Write the plain-language client brief (.md) from a "
                      "saved audit state in data/customer/.")
    brief_group = brief_p.add_mutually_exclusive_group(required=True)
    brief_group.add_argument("--all", action="store_true",
                             help="Write a brief for every company folder.")
    brief_group.add_argument("--company", default=None,
                             help="Write only for this company folder (normalized name).")
    brief_p.add_argument("--log-level", default="WARNING",
                         choices=["DEBUG", "INFO", "WARNING", "ERROR"])
