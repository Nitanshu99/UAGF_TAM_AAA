"""Command-line front door: ``python -m aaa`` / ``aaa``.

Sub-commands
------------
``aaa``            start everything configured in ``.env`` (default).
``aaa ui``         start only the Streamlit UI.
``aaa api``        start only the FastAPI backend (foreground).
``aaa audit ...``  forward to :mod:`aaa.cli` for headless audit runs.
"""
from __future__ import annotations

import logging
import sys

from aaa.launcher.config import LaunchConfig, load_config
from aaa.launcher.parse import parse_launcher_args
from aaa.launcher.procs import run_ui, start_api, stop
from aaa.launcher.services import run_migrations, start_docker


def _launch_all(cfg: LaunchConfig) -> int:
    """Bring up infrastructure and the configured app components."""
    start_docker(cfg.docker)
    run_migrations(cfg.migrate)
    api_proc = start_api(cfg.api_port) if cfg.api else None
    try:
        if cfg.ui:
            return run_ui(cfg.ui_port)
        return api_proc.wait() if api_proc else 0
    except KeyboardInterrupt:
        return 0
    finally:
        stop(api_proc)


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``aaa`` console script.

    :param argv: Argument vector (defaults to ``sys.argv[1:]``).
    :returns: Process exit code.
    """
    args, passthrough = parse_launcher_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    cfg = load_config()
    if args.component == "audit":
        from aaa.cli import main as audit_main
        return audit_main(["run", *passthrough])
    if args.component == "report":
        from aaa.cli import main as audit_main
        return audit_main(["report", *(passthrough or ["--all"])])
    if args.component == "ui":
        return run_ui(cfg.ui_port)
    if args.component == "api":
        start_docker(cfg.docker)
        run_migrations(cfg.migrate)
        proc = start_api(cfg.api_port)
        try:
            return proc.wait() if proc else 1
        except KeyboardInterrupt:
            stop(proc)
            return 0
    return _launch_all(cfg)


if __name__ == "__main__":
    sys.exit(main())
