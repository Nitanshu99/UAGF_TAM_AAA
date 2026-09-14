#!/usr/bin/env python3
"""One command from a fresh clone to a running, browsable audit.

    python3.12 bootstrap.py [--openrouter-key sk-or-v1-...] [--mock-llm] [...]

Put ``mariposa.zip`` (the intake bundle) and ``corpus.zip`` (the regulatory
corpus) in the repository root first; neither is distributed with the code.

Stage 1 — this file, standard library only — checks Python 3.12, creates
``.venv`` and installs the dependencies. Stage 2 — ``scripts.bootstrap``,
inside that venv — writes ``.env``, unpacks the bundles, starts Docker, runs the
migrations, installs Chromium, embeds the corpus into Qdrant through OpenRouter,
starts the API and the UI, and opens one browser window with every service
dashboard in its own tab and the wizard in front, filled and running.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
#: Steps across both stages; stage 2 continues the count.
TOTAL_STEPS = 10


def main() -> int:
    """Run stage 1, then hand over to stage 2 inside the venv."""
    os.chdir(REPO_ROOT)
    sys.path.insert(0, str(REPO_ROOT))
    if sys.version_info < (3, 12):
        print(f"Python 3.12+ is required; this interpreter is {sys.version.split()[0]}.\n"
              "Re-run with:  python3.12 bootstrap.py", file=sys.stderr)
        return 1
    from scripts.bootstrap.venv_stage import ensure_venv

    python = ensure_venv(TOTAL_STEPS)
    cmd = [str(python), "-m", "scripts.bootstrap", *sys.argv[1:]]
    if os.name == "nt":
        return subprocess.call(cmd)
    os.execv(cmd[0], cmd)
    return 0  # pragma: no cover - execv does not return


if __name__ == "__main__":
    sys.exit(main())
