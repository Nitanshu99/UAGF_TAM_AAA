"""Part 2 of the former ``regulatory_coverage`` module (auto-split)."""
from __future__ import annotations

from typing import TYPE_CHECKING, FrozenSet

from aaa.tools.regulatory_coverage.article_set import (  # noqa: F401
    _ADMITTED_VERDICTS,
    ARTICLE_SET,
    _resolve_article_set,
)

if TYPE_CHECKING:
    from aaa.platform.state import AuditState


def _derive_fallback_verdicts(state: AuditState, article_set: FrozenSet[str]) -> dict:
    """Populate compliance verdicts derivable from existing admitted state."""
    compliance_matrix: dict = dict(state.get("compliance_matrix", {}) or {})
    if "Art.5" in article_set and "Art.5" not in compliance_matrix:
        art5_prohibited = bool(
            state.get("art5_prohibited")
            or state.get("scope_gate", {}).get("art5_prohibited_practices_detected")
        )
        compliance_matrix["Art.5"] = "FAIL" if art5_prohibited else "PASS"
    if "Annex_IV" in article_set and "Annex_IV" not in compliance_matrix:
        intake_score = state.get("intake_completeness_score")
        if intake_score is not None:
            if intake_score >= 0.80:
                compliance_matrix["Annex_IV"] = "PASS"
            elif intake_score >= 0.50:
                compliance_matrix["Annex_IV"] = "PASS_WITH_OBSERVATIONS"
            else:
                compliance_matrix["Annex_IV"] = "FAIL"
    state["compliance_matrix"] = compliance_matrix
    return compliance_matrix
