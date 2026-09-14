"""Part 1 of the former ``index`` module (auto-split)."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def _lock(fh):
    if sys.platform == "win32":
        import msvcrt
        msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl
        fcntl.flock(fh, fcntl.LOCK_EX)


def _unlock(fh):
    if sys.platform == "win32":
        import msvcrt
        msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl
        fcntl.flock(fh, fcntl.LOCK_UN)


def _read_index(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"engagements": []}
    with path.open("r", encoding="utf-8") as fh:
        try:
            return json.load(fh)
        except json.JSONDecodeError:
            return {"engagements": []}


def _write_index(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        _lock(fh)
        try:
            json.dump(data, fh, indent=2, default=str)
        finally:
            _unlock(fh)
    tmp.replace(path)   # atomic rename
