"""Console output helpers for the bootstrap steps."""
from __future__ import annotations

import sys


def step(n: int, total: int, msg: str) -> None:
    """Print a bold cyan step banner."""
    print(f"\n\033[1;36m[{n}/{total}] {msg}\033[0m", flush=True)


def ok(msg: str) -> None:
    """Print a green success line."""
    print(f"  \033[32m✓\033[0m {msg}", flush=True)


def warn(msg: str) -> None:
    """Print a yellow warning line."""
    print(f"  \033[33m!\033[0m {msg}", flush=True)


def err(msg: str) -> None:
    """Print a red error line to stderr."""
    print(f"  \033[31m✗\033[0m {msg}", file=sys.stderr, flush=True)
