"""The Verifier verdict vocabulary, and how a critique is reduced to one."""
from __future__ import annotations

import logging
from typing import Any, Literal, Sequence

logger = logging.getLogger(__name__)

MAX_RERUNS = 2

#: The verdict recorded when the quality gate did not run. Not a judgement on
#: the artefact and not admissible as one: the deterministic fallback can check
#: that an artefact is a non-empty JSON object with a URI, and finding no fault
#: in *that* is not the same as an independent critique finding no fault (P6).
UNVERIFIED: Literal["unverified"] = "unverified"

VerifierVerdict = Literal[
    "accept", "accept_with_notes", "unverified", "rerun", "escalate_hitl"]


class VerifierError(Exception):
    """Raised when the Verifier encounters an unrecoverable configuration error."""


def decide_verdict(issues: Sequence[Any], notes: list[str], rerun_count: int) -> VerifierVerdict:
    """Translate rubric findings into a verdict code.

    Rules: no issues/notes → ``accept``; notes only → ``accept_with_notes``;
    issues with reruns left → ``rerun``; otherwise ``escalate_hitl``.
    """
    if not issues:
        return "accept_with_notes" if notes else "accept"
    if rerun_count < MAX_RERUNS:
        return "rerun"
    return "escalate_hitl"


def decide_fallback_verdict(issues: Sequence[Any], rerun_count: int) -> VerifierVerdict:
    """Translate the *deterministic* rubric's findings into a verdict code.

    The structural checks are valid where they fire — an empty artefact is
    empty whether or not a model read it — so an issue still runs the rerun
    ladder. Finding none is the case that must not read as ``accept``: the
    rubric cannot assess factual accuracy, completeness or traceability of
    reasoning, which is the whole of what the Verifier is for. Three of the
    post-fix run's sixteen critiques took this path — T15 and both delivered
    documents, T17 and T18 — and all three closed ``accept``.

    :param issues: Structural issues the rubric found.
    :param rerun_count: Reruns already consumed for this artefact.
    :returns: ``rerun``/``escalate_hitl`` on an issue, else ``unverified``.
    """
    if not issues:
        return UNVERIFIED
    return "rerun" if rerun_count < MAX_RERUNS else "escalate_hitl"
