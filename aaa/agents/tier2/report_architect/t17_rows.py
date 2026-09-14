"""One row of the T17 compliance matrix, and what an unreached article says instead."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.report_architect.constants import ARTICLE_PHASE, VALID_PHASES

#: Printed for an in-scope article the audit produced no verdict for. It names
#: the omission as an omission — the reader is owed the distinction between "we
#: assessed this and could not conclude" and "this never reached the matrix".
UNREACHED_RATIONALE = (
    "In scope for this engagement, and no verdict reached the compliance matrix: "
    "no phase produced admitted evidence for this article and no evidence gap was "
    "recorded against it. Reported as INSUFFICIENT_EVIDENCE because the audit did "
    "not assess it."
)
def _article_row(article: str, compliance_matrix: dict[str, str],
                 article_evidence: dict[str, Any]) -> dict[str, Any]:
    """Build one T17 article row, whether or not the matrix reached this article."""
    ev = article_evidence.get(article, {}) or {}
    source = ARTICLE_PHASE.get(article, "ORCH")
    verdict = compliance_matrix.get(article)
    return {
        "article": article,
        "verdict": verdict or "INSUFFICIENT_EVIDENCE",
        "evidence_uris": (ev.get("evidence_uris") or [])[:5],
        "supporting_template_ids": ev.get("supporting_template_ids", []),
        "source_phase": source if source in VALID_PHASES else "ORCH",
        "rationale": ev.get("rationale") or (None if verdict else UNREACHED_RATIONALE),
        "cgsa_control_ids": ev.get("cgsa_control_ids", []),
        "blocking_findings": ev.get("finding_ids", []),
    }


__all__ = ["UNREACHED_RATIONALE", "_article_row"]
