"""Reading the assessment fixtures on disk and the metadata each one declares."""
from __future__ import annotations

import json
import os
from typing import Any, Iterator

from aaa.tools.cgsa_pull.fixture_roots import _FIXTURE_SEARCH_DEPTH


def _fixture_files(roots: list[str]) -> Iterator[str]:
    """Yield every JSON file under ``roots``, in root order.

    The traversal mirrors :func:`aaa.tools.cgsa_pull.logger._find_fixture` — same
    bounded depth, same skipped directories — so discovery cannot offer an
    assessment that a later ``cgsa_pull`` of the same id would fail to load.
    """
    for root in roots:
        base_depth = root.rstrip(os.sep).count(os.sep)
        for dirpath, dirnames, filenames in os.walk(root):
            if dirpath.count(os.sep) - base_depth >= _FIXTURE_SEARCH_DEPTH:
                dirnames[:] = []
                continue
            dirnames[:] = [d for d in dirnames if not d.startswith((".", "__"))]
            for name in sorted(filenames):
                if name.endswith(".json"):
                    yield os.path.join(dirpath, name)
def _read(path: str) -> dict[str, Any]:
    """Parse a fixture, or an empty dict if it cannot be read."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except (OSError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}
def _metadata(path: str) -> dict[str, Any]:
    """Read a fixture's ``metadata`` block, or an empty dict if unreadable."""
    meta = _read(path).get("metadata")
    return meta if isinstance(meta, dict) else {}


__all__ = ["_fixture_files", "_metadata", "_read"]
