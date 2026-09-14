"""``python -m aaa.tools.run_preflight <case-doc> --intake-dir <bundle>``.

Exits non-zero when the planned run is not comparable with the reference, so it
can gate a paid run from a shell or a Makefile.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

from aaa.platform.env_bootstrap import load_repo_dotenv
from aaa.tools.run_preflight import BaselineError, preflight, render

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]


def _load(intake_dir: pathlib.Path, name: str) -> dict:
    """Read one stage file from an intake bundle."""
    path = intake_dir / name
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def main() -> int:
    """Run the preflight and report."""
    parser = argparse.ArgumentParser(prog="aaa.tools.run_preflight")
    parser.add_argument("doc", help="the case's per-call assessment markdown")
    parser.add_argument("--intake-dir", required=True,
                        help="bundle holding stage_a.json / stage_b.json")
    parser.add_argument("--run", default=None,
                        help="compare against this run id instead of the "
                             "controlled comparison the run archive marks")
    args = parser.parse_args()

    # The whole point is to check the environment a run would actually use.
    load_repo_dotenv(REPO_ROOT)
    intake = pathlib.Path(args.intake_dir)
    try:
        reference, checks = preflight(
            args.doc, _load(intake, "stage_a.json"), _load(intake, "stage_b.json"),
            run_id=args.run)
    except BaselineError as exc:
        print(f"preflight could not resolve the reference run:\n  {exc}", file=sys.stderr)
        return 2
    print(render(reference, checks))
    return 1 if any(c.blocking and not c.ok for c in checks) else 0


if __name__ == "__main__":
    sys.exit(main())
