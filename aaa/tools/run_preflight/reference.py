"""Locate the reference run a case's assessment document pins.

The document header is the contract. Case 06's reads::

    **Engagement** `eng-06_mariposa_edu_gmbh` · **run** `879efe44...`
    **Model** `openrouter/minimax/minimax-m3` pinned to `coreweave/fp4` · ...
    **Code** `c4666e1-dirty` · **CGSA** the real S5 export of 2026-09-03, not
    the mock fixture

Every fact needed to decide whether a new run is comparable is in those three
lines, and the run archive holds the state that run produced. What it is *not*
is ``data/customer/<company>/<engagement>_audit_state.json``: that flat file is
the most recent run under an engagement id, so a later run of the same case
silently replaces it. Case 06 has eight archived runs under one id, ranging from
46.7 % to 100 % regulatory coverage — diffing against the flat file compares
against whichever of those happened to finish last.
"""
from __future__ import annotations

import pathlib
from typing import Any

from aaa.tools.run_preflight.archived import baseline_from_index, find_archived_run
from aaa.tools.run_preflight.header import parse_header


def resolve_reference(doc_path: str | pathlib.Path,
                      run_id: str | None = None) -> dict[str, Any]:
    """Decide which run a new run should be compared against.

    Order: an explicit ``run_id``, then the controlled comparison the run
    archive marks, then the run the document header names.

    :param doc_path: The case's per-call assessment markdown.
    :param run_id: An explicit run id, overriding both.
    :returns: The parsed header with ``run_id`` and ``baseline_source`` set.
    :raises BaselineError: When no run can be resolved.
    """
    header = parse_header(doc_path)
    header["assessed_run_id"] = header["run_id"]
    if run_id:
        header["run_id"], header["baseline_source"] = run_id, "explicit"
        return header
    archived = find_archived_run(header["run_id"])
    controlled = baseline_from_index(archived.parent / "INDEX.md")
    if controlled:
        header["run_id"], header["baseline_source"] = controlled, "runs/INDEX.md"
    else:
        header["baseline_source"] = "document header"
    return header
