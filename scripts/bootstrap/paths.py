"""Repository paths the bootstrap reads and writes."""
from __future__ import annotations

from scripts.setup.paths import ENV_EXAMPLE, ENV_FILE, REPO_ROOT, VENV_DIR  # noqa: F401

#: Where the API, UI and stub write their output while the bootstrap runs.
LOG_DIR = REPO_ROOT / "logs" / "bootstrap"
#: The intake bundle the wizard is filled from (``mariposa.zip`` unpacks here).
CASE_DIR = REPO_ROOT / "mock" / "06_mariposa_edu_gmbh"
#: Where ``corpus.zip`` unpacks: the corpus directory and the checker JSON.
DATA_DIR = REPO_ROOT / "data"
