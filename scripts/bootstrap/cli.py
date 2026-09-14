"""Argument parsing for stage 2 of the bootstrap."""
from __future__ import annotations

import argparse
from pathlib import Path

from scripts.bootstrap.paths import REPO_ROOT


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the bootstrap's options.

    :param argv: Argument vector (defaults to ``sys.argv[1:]``).
    :returns: The parsed namespace.
    """
    p = argparse.ArgumentParser(
        prog="python bootstrap.py",
        description="Fresh clone → running stack → browser with every dashboard "
                    "and the wizard filled and running.",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--openrouter-key", default=None, metavar="KEY",
                   help="the one key needed (agents and embeddings both go through "
                        "OpenRouter); otherwise OPENROUTER_API_KEY from the environment "
                        "or .env, otherwise prompted")
    p.add_argument("--mock-llm", action="store_true",
                   help="spend nothing: a local stub serves embeddings and refuses chat, "
                        "so the agents take their deterministic fallbacks")
    p.add_argument("--no-run", action="store_true",
                   help="fill the wizard but do not dispatch the audit")
    p.add_argument("--headless", action="store_true",
                   help="no browser window (CI); the session is not held open")
    p.add_argument("--skip-ingest", action="store_true",
                   help="leave the Qdrant corpus as it is")
    p.add_argument("--reset-corpus", action="store_true",
                   help="drop and re-embed the corpus even if it looks current")
    p.add_argument("--zip-dir", type=Path, default=REPO_ROOT,
                   help="where mariposa.zip and corpus.zip are (default: repo root)")
    p.add_argument("--downloads", type=Path, default=REPO_ROOT / "downloads",
                   help="where the dashboard's download buttons save to")
    p.add_argument("--screenshots", type=Path, default=None, metavar="DIR",
                   help="save a PNG of every tab, the filled form and the results")
    p.add_argument("--watch-minutes", type=int, default=90,
                   help="how long to wait for the results dashboard (default 90)")
    p.add_argument("--wait-timeout", type=int, default=900,
                   help="seconds to wait for the Docker stack to be healthy (default 900)")
    return p.parse_args(argv)
