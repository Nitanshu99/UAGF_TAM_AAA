"""Initial AuditState assembly after Stage 0 completes."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.phases.initial_state import _empty_cgsa_state
from aaa.platform.state import AuditState, ClientSubmission


def assemble_state(engagement_id: str, submission: ClientSubmission,
                   stage_a_payload: dict[str, Any], gate: dict, score: float,
                   client_doc_collection: str | None,
                   artefact_uris: dict[str, str],
                   stage_c_present: bool) -> AuditState:
    """Build the fully-populated AuditState ready for Phase 1.

    :param engagement_id: Engagement identifier.
    :param submission: The assembled client submission (A + B [+ C]).
    :param stage_a_payload: Validated Stage A payload (declared values).
    :param gate: Scope-gate result block.
    :param score: Intake completeness score.
    :param client_doc_collection: Qdrant collection name, or ``None``.
    :param artefact_uris: ``{template_id: uri}`` for T01a/T01b/T01c.
    :param stage_c_present: Whether Stage C credentials were supplied.
    :returns: The initial ``AuditState``.
    """
    declared_modality = stage_a_payload["declared_modality"]
    state: AuditState = {  # type: ignore[typeddict-item]
        "engagement_id": engagement_id,
        "client_doc_collection": client_doc_collection,
        "client_submission": submission,
        "scope_gate": gate,
        "declared_modality": declared_modality,
        "declared_risk_tier": stage_a_payload["declared_risk_tier"],
        "declared_annex_iii_sections": stage_a_payload.get("declared_annex_iii_sections", []),
        # Verified values — will be populated by Phase 1.
        "risk_tier": stage_a_payload["declared_risk_tier"],
        "annex_iii_mapping": [],
        "modality": declared_modality,
        "deployment_context": stage_a_payload["deployment_context"],
        "is_llm_or_agentic": declared_modality in {"llm", "agentic", "gpai"},
        "provider_elects_third_party": stage_a_payload.get("provider_elects_third_party", False),
        # Art. 43 §3 — Annex I Section A products follow their sectoral
        # procedure, not Annex VI/VII (M18). Declared at Stage A because it
        # is a property of the product, not of the audit. Read from the contract
        # key `annex_i_section_a`; the `_acts` spelling exists only in state.
        "annex_i_section_a_acts": list(stage_a_payload.get("annex_i_section_a", []) or []),
        "harmonised_standards_applied": False,
        "declaration_verification": {},
        "art43_decision": None,
        "phase_artefacts": {
            tid: {"uri": uri, "sha256": "", "template_id": tid}
            for tid, uri in artefact_uris.items()
        },
        **_empty_cgsa_state(),
        "compliance_matrix": {},
        "blocking_findings": [],
        "positive_findings": [],
        "remediation_roadmap": [],
        "material_findings_count": None,
        "possibly_material_findings_count": None,
        "verifier_critiques": {},
        "intake_completeness_score": score,
        "completeness_score": None,
        "regulatory_coverage_pct": None,
        "final_verdict": None,
        "auditor_opinion": None,
    }
    # Mark live-system evidence as not_verifiable if Stage C absent.
    if not stage_c_present:
        state["declaration_verification"]["live_system_access"] = "not_verifiable"
    return state
