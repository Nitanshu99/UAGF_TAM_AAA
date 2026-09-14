"""``python -m scripts.results_snapshot <audit_state.json> <out.png> [--port N]``.

Renders the customer results dashboard for a finished engagement and saves a
full-page screenshot. API-driven runs (``scripts.run_mock_case``) have no browser
session, so this is how their results page is captured.
"""
from __future__ import annotations

import argparse
import pathlib

from scripts.results_snapshot.capture import capture, serve


def main() -> int:
    """Parse the arguments, serve the page, capture it, stop the server."""
    parser = argparse.ArgumentParser(prog="python -m scripts.results_snapshot")
    parser.add_argument("state", type=pathlib.Path, help="an *_audit_state.json the run wrote")
    parser.add_argument("out", type=pathlib.Path, help="where to write the PNG")
    parser.add_argument("--port", type=int, default=18599)
    args = parser.parse_args()
    server = serve(args.state, args.port)
    try:
        capture(f"http://localhost:{args.port}", args.out)
    finally:
        server.terminate()
        server.wait(timeout=30)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
