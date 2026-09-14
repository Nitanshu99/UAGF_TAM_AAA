"""Deterministic fallback critique (used when the LLM call fails)."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.verifier.verdicts import UNVERIFIED, decide_fallback_verdict


def fallback_critique(
    agent: Any,
    phase_id: str,
    template_id: str,
    content: Any,
    evidence_uris: list[str],
    rerun_count: int,
    artefact_uri: str = "",
    reason: str = "",
) -> dict[str, Any]:
    """Deterministic rubric checks that run without an LLM.

    Applied checks: content is non-empty; content is a dict (schema-valid
    JSON object); traceability — a persisted artefact URI and/or evidence
    URIs exist.

    Clearing those checks is recorded as ``unverified``, not ``accept``: they
    establish that an artefact is *well-formed*, and the four dimensions the
    Verifier exists to judge were never assessed (P6). The note says so in
    words, because a reader of the critique is entitled to know that the
    absence of issues is the absence of a critique.

    :param agent: The Verifier instance (prompt metadata provenance).
    :param reason: The failure that sent the critique down this path, recorded
        so the trail distinguishes a timeout from a provider outage.
    :returns: A ``VerifierCritique``-shaped dict with ``llm_fallback_mode``.
    """
    # Structured like the LLM path's issues (M12), so the Orchestrator's
    # `_blocking_issues` filter sees a fallback's findings too. An empty
    # artefact is a critical defect whichever path noticed it.
    issues: list[dict[str, Any]] = []
    notes: list[str] = []

    if not content:
        issues.append({"severity": "critical", "field": "content",
                       "description": "Artefact content is empty.",
                       "recommendation": "Re-run the phase; the artefact stored no content."})
    if isinstance(content, dict) and len(content) == 0:
        issues.append({"severity": "critical", "field": "content",
                       "description": "Artefact payload is an empty dict.",
                       "recommendation": "Re-run the phase; the artefact stored no fields."})
    if not artefact_uri and not evidence_uris:
        notes.append("No artefact URI or evidence URIs provided; linkage cannot be verified.")

    verdict = decide_fallback_verdict(issues, rerun_count)
    if verdict == UNVERIFIED:
        notes.append(
            "Independent verification did not run"
            + (f" ({reason})" if reason else "")
            + "; only deterministic structural checks were applied. This "
              "artefact is unverified, not accepted.")
    return {
        "phase_id": phase_id,
        "template_id": template_id,
        "verdict": verdict,
        "issues": issues,
        "notes": notes,
        "article_citations": [],
        "scores": {},
        "total_score": None,
        "materiality_assessments": [],
        "declaration_mismatches": [],
        "llm_fallback_mode": True,
        "prompt_metadata": agent.prompt_metadata("verifier", True),
        "rerun_required": verdict == "rerun",
        "unverified_reason": reason or "the Verifier's LLM critique failed",
    }
