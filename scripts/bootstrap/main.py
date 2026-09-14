"""Stage 2 orchestration: steps 3–10 in order, children stopped on the way out."""
from __future__ import annotations

import signal
import sys

from scripts.bootstrap.cli import parse_args
from scripts.bootstrap.orchestrate import (
    PYTHON,
    TOTAL,
    Children,
    mock_overrides,
    prepare,
    serve_and_browse,
)
from scripts.bootstrap.steps.app import stop


def _interrupt(signum: int, frame: object) -> None:
    """Turn SIGTERM into the KeyboardInterrupt the clean-up path already handles."""
    raise KeyboardInterrupt


def _line_buffer_stdout() -> None:
    """Flush per line even when the output is a file — a run is watched through its log."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(line_buffering=True)  # type: ignore[union-attr]
        except (AttributeError, ValueError):
            pass


def main(argv: list[str] | None = None) -> int:
    """Run stage 2 end to end.

    :param argv: Argument vector (defaults to ``sys.argv[1:]``).
    :returns: Process exit code.
    """
    args = parse_args(argv)
    children: Children = {}
    _line_buffer_stdout()
    # `pkill -f scripts.bootstrap` (the stop hint) sends SIGTERM; without this
    # the parked process would die at once and orphan the API, UI and stub.
    signal.signal(signal.SIGTERM, _interrupt)
    try:
        prepare(args, children)
        serve_and_browse(args, children)
    except KeyboardInterrupt:
        print("\n  interrupted.")
        return 130
    finally:
        for name in ("ui", "api", "stub"):
            stop(children.get(name))
        print("\n  Docker stack left running (data kept). Stop it with:\n"
              "    docker compose --profile obs --profile ui down")
    return 0


__all__ = ["Children", "PYTHON", "TOTAL", "main", "mock_overrides"]
