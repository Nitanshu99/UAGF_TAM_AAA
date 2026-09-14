"""Declaration diffing and Art. 43 selection for Phase 1."""
from __future__ import annotations

from typing import Any

from aaa.platform.state import AnnexIIIEntry
from aaa.tools.art43_select import art43_select_from_state
from aaa.tools.declaration_diff import declaration_diff, diff_annex_iii_sections


def build_verification_map(t01a: dict, decl: dict, verified_modality: str,
                           verified_risk_tier: str, is_llm_or_agentic: bool,
                           declared_sections: list, verified_sections: list) -> dict:
    """Diff declared values against Phase 1 verified values.

    :returns: The ``declaration_verification`` map (match/mismatch/…).
    """
    shared = {
        "deployment_context": t01a.get("deployment_context", ""),
        "provider_elects_third_party": t01a.get("provider_elects_third_party", False),
        "gdpr_overlap": t01a.get("gdpr_overlap", False),
        "special_category_data": t01a.get("special_category_data", False),
        "gpai_general_purpose": t01a.get("gpai_general_purpose", False),
    }
    declared_vals = {
        "modality": t01a.get("declared_modality", ""),
        "risk_tier": t01a.get("declared_risk_tier", ""),
        "is_llm_or_agentic": t01a.get("declared_modality", "") in {"llm", "agentic", "gpai"},
        **shared,
    }
    verified_vals = {
        "modality": verified_modality,
        "risk_tier": verified_risk_tier,
        "is_llm_or_agentic": is_llm_or_agentic,
        **shared,
    }
    verification_map = declaration_diff(declared_vals, verified_vals)
    verification_map.update(diff_annex_iii_sections(declared_sections, verified_sections))
    # Preserve Stage C not_verifiable if set
    if decl.get("live_system_access") == "not_verifiable":
        verification_map["live_system_access"] = "not_verifiable"
    return verification_map


def decide_art43(t01a: dict, verified_risk_tier: str, annex_entries: list[AnnexIIIEntry],
                 decl: dict | None = None) -> tuple[dict, str | None, bool, dict]:
    """Run the final Art. 43 selection and compare with the Stage A preview.

    ``harmonised_standards_applied`` comes from the dispatch, which carries the
    state value: the T01a contract cannot hold it, so reading it from T01a was
    always ``False``. Section A acts come from T01a under their contract key
    ``annex_i_section_a`` (T-20260913-016).

    :returns: ``(art43_decision, preview_procedure, delta, pseudo_state)``.
    """
    pseudo_state: dict[str, Any] = {
        "risk_tier": verified_risk_tier,
        "annex_iii_mapping": [
            {"annex_iii_section": e["annex_iii_section"]} for e in annex_entries
            if e["provenance"] != "phase1_rejected"
        ],
        # Set by Phase 5, from the CGSA, two phases after this decision is made.
        # Read rather than asserted (M10): the literal that stood here made the
        # Phase 1 decision unable to see the value even on a re-entry that had
        # it, and stated `False` as a verified input rather than an undetermined
        # one. `node_compliance_matrix` recomputes from the completed state and
        # `reconcile_art43` reports any disagreement with what was stored here.
        "harmonised_standards_applied": bool(
            (decl or {}).get("harmonised_standards_applied", False)),
        "provider_elects_third_party": t01a.get("provider_elects_third_party", False),
        "annex_i_section_a_acts": list(t01a.get("annex_i_section_a", []) or []),
    }
    art43 = art43_select_from_state(pseudo_state, use_declared=False)
    preview_procedure = t01a.get("art43_preview")
    delta = (preview_procedure is not None and preview_procedure != art43["procedure"])
    # dict()/bool(): match the declared plain-dict/bool return contract.
    return dict(art43), preview_procedure, bool(delta), pseudo_state
