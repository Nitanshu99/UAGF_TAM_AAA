"""Part 2 of the former ``index`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from aaa.data.index.lock import _lock, _read_index, _unlock, _write_index  # noqa: F401
from aaa.data.paths import index_path


def upsert(entry: dict[str, Any]) -> None:
    """Insert or update the index entry for one engagement.

    ``entry`` must contain ``engagement_id``; all other keys are merged
    with any existing row for that ID.
    """
    path = index_path()
    data = _read_index(path)
    eid = entry["engagement_id"]
    rows: list[dict[str, Any]] = data.setdefault("engagements", [])
    for i, row in enumerate(rows):
        if row.get("engagement_id") == eid:
            rows[i] = {**row, **entry}
            break
    else:
        rows.append(entry)
    _write_index(path, data)


def get(engagement_id: str) -> dict[str, Any] | None:
    """Return the index summary for *engagement_id*, or ``None``."""
    data = _read_index(index_path())
    for row in data.get("engagements", []):
        if row.get("engagement_id") == engagement_id:
            return row
    return None


def list_all() -> list[dict[str, Any]]:
    """Return all index entries, newest-first by ``created_at``."""
    data = _read_index(index_path())
    rows = data.get("engagements", [])
    return sorted(rows, key=lambda r: r.get("created_at", ""), reverse=True)


def delete(engagement_id: str) -> bool:
    """Remove an engagement from the index.  Returns True if it existed."""
    path = index_path()
    data = _read_index(path)
    before = len(data.get("engagements", []))
    data["engagements"] = [
        r for r in data.get("engagements", [])
        if r.get("engagement_id") != engagement_id
    ]
    if len(data["engagements"]) < before:
        _write_index(path, data)
        return True
    return False


__all__ = ["upsert", "get", "list_all", "delete"]
