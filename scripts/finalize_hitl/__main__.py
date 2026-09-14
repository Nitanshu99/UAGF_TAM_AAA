"""``python -m scripts.finalize_hitl`` entry point."""
from __future__ import annotations

import sys

from scripts.finalize_hitl.finalize import main

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python -m scripts.finalize_hitl <engagement_id>", file=sys.stderr)
        print("  e.g. python -m scripts.finalize_hitl eng-01_finclear_gmbh",
              file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
