"""Find a client's CGSA assessment from the identity they already gave us.

``cgsa_pull`` answers "fetch assessment X". This module answers the question
that comes before it: *which* assessment belongs to this client. The wizard
used to ask the customer for the id outright — a field nobody outside this
repository could fill, since the id is minted by S4 and never shown to the
organisation it describes. Every assessment already names its subject
(``metadata.organisation_name`` and ``metadata.system_under_audit``), and the
customer types exactly those two things in step 0, so the lookup is ours to do.

Silence is the failure mode by design: no match means Phase 5 proceeds without
a prior self-assessment, which is the same position a first-time client is in.
An ambiguous match is also silence — guessing between two assessments would
attach the wrong governance history to an audit.
"""
from __future__ import annotations

import logging
from typing import Any

from aaa.tools.cgsa_pull.compat import is_evaluated
from aaa.tools.cgsa_pull.fixture_roots import fixture_roots
from aaa.tools.cgsa_pull.fixtures import _fixture_files, _read

logger = logging.getLogger(__name__)















def discover_assessments(roots: list[str] | None = None) -> list[dict[str, Any]]:
    """Every CGSA assessment reachable from the configured fixture roots.

    :param roots: Directories to search; defaults to :func:`fixture_roots`.
    :returns: One record per assessment id — ``assessment_id``,
        ``organisation_name``, ``system_under_audit``, ``path``, ``evaluated``.
    """
    found: dict[str, dict[str, Any]] = {}
    for path in _fixture_files(fixture_roots() if roots is None else roots):
        payload = _read(path)
        meta = payload.get("metadata")
        meta = meta if isinstance(meta, dict) else {}
        assessment_id = str(meta.get("assessment_id") or "")
        # First root wins, matching `_find_fixture`'s precedence: four
        # assessments exist in both `mock/` and `scripts/fixtures/` and have
        # drifted, so discovery must name the copy the pull will actually read.
        if not assessment_id or assessment_id in found:
            continue
        found[assessment_id] = {
            "assessment_id": assessment_id,
            "organisation_name": str(meta.get("organisation_name") or ""),
            "system_under_audit": str(meta.get("system_under_audit") or ""),
            "path": path,
            # Whether this export can produce control-level non-conformities at
            # all; see `resolve_assessment_id` for why it decides a tie.
            "evaluated": is_evaluated(payload),
        }
    return list(found.values())
