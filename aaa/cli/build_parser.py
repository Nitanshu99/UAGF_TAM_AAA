"""Part 4 of the former ``cli`` module (auto-split)."""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import pathlib
import sys

from aaa.cli.cmd.run import _cmd_run  # noqa: F401
from aaa.cli.logger import _load_json, _summarise, logger  # noqa: F401
from aaa.cli.parsers import add_brief_parser, add_report_parser, add_run_parser
from aaa.cli.seed.intake import _seed_intake  # noqa: F401


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m aaa.cli",
        description="AAA — Autonomous AI Auditor CLI (§11).",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    add_run_parser(sub)
    add_report_parser(sub)
    add_brief_parser(sub)
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: parse args and dispatch to the selected sub-command."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(level=getattr(logging, args.log_level))

    if getattr(args, "cgsa_fixture_dir", None):
        os.environ["CGSA_FIXTURE_DIR"] = str(
            pathlib.Path(args.cgsa_fixture_dir).resolve()
        )

    if args.command == "run":
        try:
            return asyncio.run(_cmd_run(args))
        except Exception as exc:  # noqa: BLE001
            logger.exception("Pipeline crashed: %s", exc)
            print(f"[cli] pipeline error: {exc}", file=sys.stderr)
            return 3
    if args.command == "report":
        from aaa.cli.cmd.report import _cmd_report
        return _cmd_report(args)
    if args.command == "brief":
        from aaa.cli.cmd.brief import _cmd_brief
        return _cmd_brief(args)
    return 3


if __name__ == "__main__":
    sys.exit(main())
