"""Part 8 of the former ``phase_runners`` module (auto-split)."""
from __future__ import annotations

from aaa.agents.tier1.phases.phase_runners.logger import logger  # noqa: F401
from aaa.agents.tier1.phases.phase_runners.phase.p1 import run_phase_1  # noqa: F401
from aaa.agents.tier1.phases.phase_runners.phase.p2 import run_phase_2  # noqa: F401
from aaa.agents.tier1.phases.phase_runners.phase.p3 import run_phase_3  # noqa: F401
from aaa.agents.tier1.phases.phase_runners.phase.p4 import run_phase_4  # noqa: F401
from aaa.agents.tier1.phases.phase_runners.phase.p5 import run_phase_5  # noqa: F401
from aaa.agents.tier1.phases.phase_runners.uagf_tam_l import run_uagf_tam_l  # noqa: F401


def _phase6_declaration_summary(state: dict, eng: str, stage_a: dict) -> dict:
    """Build the full evidence surface handed to the ReportArchitect."""
    return {
        "engagement_id": eng,
        "risk_tier": state.get("risk_tier", "high"),
        "modality": state.get("modality", "tabular"),
        "deployment_context": state.get("deployment_context", "b2b"),
        "is_llm_or_agentic": state.get("is_llm_or_agentic", False),
        "final_verdict": state.get("final_verdict"),
        "compliance_matrix": state.get("compliance_matrix", {}),
        # ── full evidence surface so the report is populated + traceable ──
        "stage_a": stage_a,
        "annex_iii_sections": state.get("declared_annex_iii_sections", []),
        "art43_decision": state.get("art43_decision"),
        "phase_artefacts": state.get("phase_artefacts", {}),
        "verifier_critiques": state.get("verifier_critiques", {}),
        "article_evidence": state.get("article_evidence", {}),
        "blocking_findings": state.get("blocking_findings", []),
        "positive_findings": state.get("positive_findings", []),
        "remediation_roadmap": state.get("remediation_roadmap", []),
        "material_findings_count": state.get("material_findings_count"),
        "intake_completeness_score": state.get("intake_completeness_score"),
        "completeness_score": state.get("completeness_score"),
        "regulatory_coverage_pct": state.get("regulatory_coverage_pct"),
        "opinion_disclaimer": state.get("opinion_disclaimer", False),
        "hitl_required": state.get("hitl_required", False),
        "hitl_reason": state.get("hitl_reason"),
        # Present only when the ReAct loop ended in the deterministic
        # wrap-up; names the phases it had to force and any it could not.
        "react_termination": state.get("react_termination"),
        # Phases that closed below the confidence floor; their articles are in
        # `insufficient_evidence_articles` and belong in the limitations. (F5)
        "low_confidence_phases": state.get("low_confidence_phases", []),
        # Artefacts the Verifier did not admit, with the verdict and reason for
        # each; the ReportArchitect must be able to say so rather than present
        # them as admitted evidence. (P6/Q1)
        "unadmitted_artefacts": state.get("unadmitted_artefacts", []),
        # Procedures not performed, and whether each removed an article's evidence.
        "scope_limitations": state.get("scope_limitations", []),
        "cgsa_domain_scores": state.get("cgsa_domain_scores", {}),
        "cgsa_report_url": state.get("cgsa_report_url"),
    }
