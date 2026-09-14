"""``python -m scripts.bootstrap`` entry point."""
from __future__ import annotations

import sys

from scripts.bootstrap.main import main

if __name__ == "__main__":
    sys.exit(main())
