"""Finding the archived run a baseline document refers to, and the state it left behind."""
from __future__ import annotations

import json
import pathlib
from typing import Any

from aaa.tools.run_preflight.header import _CONTROLLED, BaselineError


def find_archived_run(run_id: str, root: str = "data/customer") -> pathlib.Path:
    """Find the archived run directory whose ``run.json`` carries ``run_id``.

    A prefix is accepted: ``INDEX.md`` names runs by the eight-character stem
    that also names the directory, while the case document quotes the full id.

    :param run_id: The run id, or a unique prefix of it.
    :param root: Customer deliverable root.
    :returns: The run directory.
    :raises BaselineError: When no archived run matches, or several do.
    """
    hits = []
    for candidate in sorted(pathlib.Path(root).glob("*/runs/*/run.json")):
        try:
            with candidate.open("r", encoding="utf-8") as fh:
                if str(json.load(fh).get("run_id") or "").startswith(run_id):
                    hits.append(candidate.parent)
        except (OSError, ValueError):
            continue
    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1:
        raise BaselineError(
            f"run {run_id!r} is a prefix of {len(hits)} archived runs; quote more of it.")
    raise BaselineError(
        f"run {run_id} is named by the document but is not in the run archive "
        f"under {root}; there is nothing to compare a new run against.")
def reference_state(run_dir: pathlib.Path) -> dict[str, Any]:
    """Load the AuditState the reference run produced.

    :param run_dir: An archived run directory.
    :returns: The parsed AuditState.
    :raises BaselineError: When the directory holds no audit state.
    """
    states = sorted(run_dir.glob("*_audit_state.json"))
    if not states:
        raise BaselineError(f"{run_dir} holds no audit state")
    with states[0].open("r", encoding="utf-8") as fh:
        return json.load(fh)
def baseline_from_index(index_path: str | pathlib.Path) -> str | None:
    """The run ``runs/INDEX.md`` marks as the controlled comparison.

    The case document header names the run that was *assessed*, which is the
    pre-fix one — comparing a new run against it measures the fix series rather
    than the new run. The archive index is the only record of which directory
    holds the controlled post-fix comparison, because ``run.json`` stamps the
    same dirty revision on every run in the series.

    :param index_path: Path to the engagement's ``runs/INDEX.md``.
    :returns: The run id, or ``None`` when the index marks none.
    """
    path = pathlib.Path(index_path)
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    for match in _CONTROLLED.finditer(text):
        if "CONTROLLED COMPARISON" in match.group("body").upper():
            return match.group("run")
    return None


__all__ = ["baseline_from_index", "find_archived_run", "reference_state"]
