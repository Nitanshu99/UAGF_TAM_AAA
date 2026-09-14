"""Names every orchestration step shares: the step count, the interpreter, the child table."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

#: How many numbered steps the two bootstrap stages print.
TOTAL = 10
#: The interpreter stage 1 handed over to; every child runs under it.
PYTHON = Path(sys.executable)
#: The long-lived children stage 2 starts, by role, so the exit path can stop them.
Children = dict[str, "subprocess.Popen | None"]

__all__ = ["Children", "PYTHON", "TOTAL"]
