"""Customer-folder discovery and JSON persistence."""
from __future__ import annotations

import json
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def find_customer_dir(engagement_id: str) -> tuple[pathlib.Path | None, pathlib.Path | None]:
    """Locate the customer folder holding the engagement's audit state.

    :param engagement_id: Engagement identifier.
    :returns: ``(customer_dir, audit_state_path)`` or ``(None, None)``.
    """
    base = REPO_ROOT / "data" / "customer"
    if not base.exists():
        return None, None
    for sub in sorted(base.iterdir()):
        state_path = sub / f"{engagement_id}_audit_state.json"
        if state_path.exists():
            return sub, state_path
    return None, None


def write_json(path: pathlib.Path, payload: object) -> None:
    """Write *payload* to *path* as pretty-printed JSON.

    :param path: Destination file.
    :param payload: JSON-serialisable object.
    """
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
