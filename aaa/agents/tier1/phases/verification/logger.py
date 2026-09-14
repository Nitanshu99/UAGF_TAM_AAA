"""Part 1 of the former ``verification`` module (auto-split)."""
from __future__ import annotations

import logging
from typing import Any

from aaa.agents.tier1.verifier import Verifier

logger = logging.getLogger(__name__)


# `unverified` sits above admission and below `rerun` deliberately. It must not
# be admitted (the gate did not run), and it must not outrank a `rerun`: when
# one artefact of a phase is unverified and another is rejected, the phase is
# re-dispatched, which re-critiques both — the cheapest retry of the Verifier
# available without a retry mechanism of its own (P6).
_VERDICT_ORDER = ["accept", "accept_with_notes", "unverified", "rerun", "escalate_hitl"]


_REPORT_TIDS = {"T17_compliance_matrix", "T18_audit_report"}


_VERIFIER: Verifier | None = None


def _get_verifier(regulatory_rag: Any = None) -> Verifier:
    """Return a process-wide Verifier (cheap to construct; reused across phases).

    The RAG arrives with the engagement rather than at import, so the singleton
    adopts the first real one it is offered. Adoption is one-way — a later
    ``None`` never strips it — for the reason fix 12 made ``bind_engagement_id``
    a narrowing: a caller that happens not to hold the RAG must not disarm the
    Verifier's citation check for every phase that follows.

    :param regulatory_rag: The engagement's RegulatoryRAG, if the caller has one.
    :type regulatory_rag: Any
    :returns: The process-wide Verifier.
    :rtype: Verifier
    """
    global _VERIFIER  # pylint: disable=global-statement
    if _VERIFIER is None:
        _VERIFIER = Verifier(regulatory_rag=regulatory_rag)
    elif regulatory_rag is not None and _VERIFIER.rag is None:
        _VERIFIER.rag = regulatory_rag
    return _VERIFIER


def _worse(a: str, b: str) -> str:
    ia = _VERDICT_ORDER.index(a) if a in _VERDICT_ORDER else 0
    ib = _VERDICT_ORDER.index(b) if b in _VERDICT_ORDER else 0
    return _VERDICT_ORDER[max(ia, ib)]


def _artefact_uri(state: dict, tid: str) -> str:
    """Return the persisted MinIO URI for an artefact, or '' if absent."""
    ref = state.get("phase_artefacts", {}).get(tid)
    return ref.get("uri", "") if isinstance(ref, dict) else ""


def _artefact_content(store: Any, state: dict, tid: str) -> Any:
    """Load a produced artefact's content from the store for critique."""
    uri = _artefact_uri(state, tid)
    if not uri:
        return {}
    try:
        return store.get_artefact(uri) or {}
    except Exception:  # noqa: BLE001
        return {}
