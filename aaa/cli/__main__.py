"""Module entry point so ``python -m aaa.cli`` runs the audit CLI."""
from __future__ import annotations

import sys

from aaa.cli import main

if __name__ == "__main__":
    sys.exit(main())
