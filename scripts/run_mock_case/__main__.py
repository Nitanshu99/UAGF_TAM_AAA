"""``python -m scripts.run_mock_case`` entry point."""
from __future__ import annotations

import sys

from scripts.run_mock_case.runner import main

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python -m scripts.run_mock_case <case-folder-name>",
              file=sys.stderr)
        print("  e.g. python -m scripts.run_mock_case 01_finclear_gmbh",
              file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
