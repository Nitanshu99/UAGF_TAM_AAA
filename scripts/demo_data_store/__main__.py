"""``python -m scripts.demo_data_store`` entry point."""
from __future__ import annotations

import os

# The demo defaults its data directory before importing modules that read it.
os.environ.setdefault("AAA_DATA_DIR", "/tmp/aaa_demo_data")

# pylint: disable=wrong-import-position
from scripts.demo_data_store.readback import read_back  # noqa: E402
from scripts.demo_data_store.seed import seed  # noqa: E402

if __name__ == "__main__":
    seed()
    read_back()
