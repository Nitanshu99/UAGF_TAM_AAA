"""Parsing the baseline document's header into the reference state it describes."""
from __future__ import annotations

import pathlib
import re
from typing import Any

_ENGAGEMENT = re.compile(r"\*\*Engagement\*\*\s*`([^`]+)`")
_RUN = re.compile(r"\*\*run\*\*\s*`([0-9a-f]{8,})`")
_MODEL = re.compile(r"\*\*Model\*\*\s*`([^`]+)`(?:\s*pinned to\s*`([^`]+)`)?")
_CGSA_NOTE = re.compile(r"\*\*CGSA\*\*\s*(.+?)\s*$", re.MULTILINE)
_KPI_ROW = re.compile(r"^\|\s*([^|]+?)\s*\|\s*\*{0,2}([^|*]+?)\*{0,2}\s*\|\s*$", re.MULTILINE)
#: How ``runs/INDEX.md`` marks the run a new run should be compared against.
#: The archive holds eight runs of case 06 spanning 46.7 %–100 % coverage; only
#: this line separates the controlled comparison from the pre-fix assessed run
#: the case document's own header names, and from five discarded attempts.
_CONTROLLED = re.compile(
    r"`(?P<dir>[0-9A-Za-z_]+__[0-9a-f]{8})`\*{0,2}\s*—\s*run\s*`(?P<run>[0-9a-f]{8,})`"
    r"[^\n]*\n(?P<body>(?:[^\n]*\n){1,3})", re.MULTILINE)
#: How far into the document the header is read. The header is the first block;
#: the rest is 78 000 lines of per-call transcript.
_HEADER_LINES = 40
class BaselineError(Exception):
    """Raised when the baseline run a document points at cannot be resolved."""
def parse_header(doc_path: str | pathlib.Path) -> dict[str, Any]:
    """Read the pinned engagement, run id, model and CGSA note from a case doc.

    :param doc_path: Path to the per-call assessment markdown.
    :returns: ``engagement_id``, ``run_id``, ``model``, ``provider_pin``,
        ``cgsa_note`` and the header KPI table as ``kpis``.
    :raises BaselineError: When the header names no run.
    """
    path = pathlib.Path(doc_path)
    if not path.is_file():
        # Case 06's document is gitignored client material, so a clone legitimately
        # does not have it. Say which file and why, rather than a FileNotFoundError
        # traceback from inside the parser.
        raise BaselineError(
            f"{path} is not present. A case's per-call assessment document is the "
            "contract a run is checked against; where the case is real-client "
            "material the document is not distributed with the repository. Point "
            "--doc at the copy you hold, or skip the preflight.")
    with path.open("r", encoding="utf-8") as fh:
        head = "".join(next(fh, "") for _ in range(_HEADER_LINES))
    run = _RUN.search(head)
    if run is None:
        raise BaselineError(f"{path}: header names no run id")
    model = _MODEL.search(head)
    engagement = _ENGAGEMENT.search(head)
    note = _CGSA_NOTE.search(head)
    kpis = {k.strip().lower(): v.strip() for k, v in _KPI_ROW.findall(head)
            if k.strip().lower() not in {"kpi", "---"}}
    return {
        "doc": str(path),
        "engagement_id": engagement.group(1) if engagement else None,
        "run_id": run.group(1),
        "model": model.group(1) if model else None,
        "provider_pin": model.group(2) if model and model.group(2) else None,
        "cgsa_note": note.group(1) if note else None,
        "kpis": kpis,
    }


__all__ = ["BaselineError", "_CGSA_NOTE", "_CONTROLLED", "_ENGAGEMENT", "_HEADER_LINES", "_KPI_ROW", "_MODEL", "_RUN", "parse_header"]
