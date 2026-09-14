"""Atomic JSON write helpers and company-name slugging."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def normalized_company_name(name: str | None) -> str:
    """Slugify a provider/company name for a filesystem folder.

    ``"FinClear GmbH"`` → ``"finclear_gmbh"``; empty/None → ``"unknown_provider"``.

    :param name: Raw provider name.
    :returns: Filesystem-safe slug.
    """
    slug = re.sub(r"[^a-z0-9]+", "_", (name or "").strip().lower()).strip("_")
    return slug or "unknown_provider"


def _write(path: Path, data: Any) -> None:
    """Write *data* as JSON to *path* atomically (tmp-then-rename).

    :param path: Destination file path.
    :param data: JSON-serialisable payload.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, default=str)
    tmp.replace(path)


def _append_list(path: Path, item: dict[str, Any]) -> None:
    """Append *item* to a JSON array file (creates the file if absent).

    :param path: Target JSON array file.
    :param item: Entry to append.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    existing: list[dict[str, Any]] = []
    if path.exists():
        try:
            existing = json.loads(path.read_text("utf-8"))
        except (json.JSONDecodeError, OSError):
            existing = []
    existing.append(item)
    _write(path, existing)
