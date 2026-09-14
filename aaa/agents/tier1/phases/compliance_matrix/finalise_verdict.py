"""Part 9 of the former ``compliance_matrix`` module (auto-split)."""
from __future__ import annotations

from aaa.agents.tier1.phases.compliance_matrix.collect_admitted_articles import (  # noqa: F401
    _collect_admitted_articles,
)
from aaa.agents.tier1.phases.compliance_matrix.compute_final_verdict import (  # noqa: F401
    _compute_final_verdict,
)
from aaa.agents.tier1.phases.compliance_matrix.derive_verdicts import _derive_verdicts  # noqa: F401
from aaa.agents.tier1.phases.compliance_matrix.evidence_entry import _evidence_entry  # noqa: F401
from aaa.agents.tier1.phases.compliance_matrix.findings_by_article import (  # noqa: F401
    _cgsa_controls_for,
    _findings_by_article,
)
from aaa.agents.tier1.phases.compliance_matrix.logger import (  # noqa: F401
    _ADMITTED_VERDICTS,
    _CORE_HIGH_RISK_ARTICLES,
    _TEMPLATE_ARTICLES,
    _core_article,
    logger,
)
from aaa.agents.tier1.phases.compliance_matrix.rationale import _rationale  # noqa: F401
from aaa.agents.tier1.phases.compliance_matrix.supporting_tids import (  # noqa: F401
    _article_verdict,
    _supporting_tids,
)


def _finalise_verdict(state: dict) -> None:
    """Set the final verdict, materiality counts, and completion log line."""
    verdict = _compute_final_verdict(state)
    state["final_verdict"] = verdict
    state["material_findings_count"] = sum(
        1 for f in state.get("blocking_findings", [])
        if f.get("materiality") == "material")
    state["possibly_material_findings_count"] = sum(
        1 for f in state.get("blocking_findings", [])
        if f.get("materiality") == "possibly_material")
    logger.info(
        "Engagement %s final_verdict=%s (cs=%.2f rc=%.1f, disclaimer=%s)",
        state["engagement_id"], verdict,
        state.get("completeness_score") or 0.0,
        state.get("regulatory_coverage_pct") or 0.0,
        state.get("opinion_disclaimer"))
