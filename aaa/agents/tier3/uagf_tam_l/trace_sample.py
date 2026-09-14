"""Resolves the client-submitted agentic trace sample for trajectory_audit.

``trace_sample_uri`` (Annex IV, agentic-only) points at a JSON array of trace
objects the client exported from their own tracing (Langfuse-shaped or
equivalent). Absent/unparseable → an empty list, so ``trajectory_audit``
falls back to its honest zero-evidence result rather than raising.
"""
from __future__ import annotations

import logging
from typing import Any

from aaa.agents.tier3.uagf_tam_l.rows import unwrap_rows

logger = logging.getLogger(__name__)


def resolve_trace_sample(stage_b: dict[str, Any], store: Any) -> list[dict[str, Any]]:
    """Load and validate the trace sample referenced by ``trace_sample_uri``.

    :param stage_b: The Annex IV dossier (may lack ``trace_sample_uri``).
    :type stage_b: dict[str, Any]
    :param store: Evidence store used to resolve ``minio://`` URIs.
    :type store: Any
    :returns: A list of trace dicts, or ``[]`` when absent/unparseable.
    :rtype: list[dict[str, Any]]
    """
    uri = stage_b.get("trace_sample_uri")
    if not uri:
        return []
    try:
        from aaa.platform.artifact_loader import load_artifact_from_uri
        traces = load_artifact_from_uri(uri, store, "json")
    except Exception as exc:  # noqa: BLE001 — best-effort; caller treats [] as no-evidence
        logger.warning("trace_sample_uri %s could not be loaded: %s", uri, exc)
        return []
    # Same wrapper blindness the golden set had: an export is far more often
    # `{"traces": [...]}` than a bare array.
    rows = unwrap_rows(traces)
    if not rows:
        logger.warning("trace_sample_uri %s contained no trace objects; ignoring.", uri)
    return rows
