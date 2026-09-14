"""Module entry point so ``python -m aaa`` starts the platform launcher."""
from __future__ import annotations

import sys

from aaa.launcher.cli import main

if __name__ == "__main__":
    sys.exit(main())
