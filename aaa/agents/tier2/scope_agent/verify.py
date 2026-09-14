"""The deterministic Phase 1 verification pipeline."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.scope_agent.checks import check_art5, determine_risk_tier, verify_modality
from aaa.agents.tier2.scope_agent.context import build_context
from aaa.agents.tier2.scope_agent.derogation import stamp_declared_derogation
from aaa.agents.tier2.scope_agent.diffing import build_verification_map, decide_art43
from aaa.agents.tier2.scope_agent.errors import ScopeAgentError
from aaa.tools.annex_iii_classify import annex_iii_classify
from aaa.tools.scope_gate.scopeverdict import _art50_flag


def run_verification(agent: Any, t01a: dict, t01b: dict, decl: dict,
                     message: dict, engagement_id: str,
                     system_desc: str) -> dict[str, Any]:
    """Classify, gate, and diff the declaration; return the phase context.

    :param agent: The ScopeAgent (provides the RAG handle).
    :raises ScopeAgentError: When an Art. 5 prohibition is detected.
    :returns: The processing context consumed by the artefact builders.
    """
    declared_sections = t01a.get("declared_annex_iii_sections", [])
    annex_entries = annex_iii_classify(
        declared_sections=declared_sections, system_description=system_desc)
    stamp_declared_derogation(annex_entries, t01a)

    art5_prohibited, art5_basis = check_art5(system_desc)
    if art5_prohibited:
        raise ScopeAgentError(
            reason=f"Art. 5 prohibited practice detected: {art5_basis}",
            details={"art5_basis": art5_basis,
                     "system_description_excerpt": system_desc[:300]})

    verified_modality = verify_modality(t01a, t01b)
    is_llm_or_agentic = verified_modality in {"llm", "agentic", "gpai"}
    verified_sections = [
        e["annex_iii_section"] for e in annex_entries
        if e["provenance"] in {"client_declared", "phase1_verified", "phase1_corrected"}
    ]
    verified_risk_tier = determine_risk_tier(
        t01a.get("declared_risk_tier", "minimal"), verified_sections, is_llm_or_agentic,
        _art50_flag(t01a) if "art50_transparency_triggers" in t01a else None)
    verification_map = build_verification_map(
        t01a, decl, verified_modality, verified_risk_tier, is_llm_or_agentic,
        declared_sections, verified_sections)
    art43, preview_procedure, art43_delta, pseudo_state = decide_art43(
        t01a, verified_risk_tier, annex_entries, decl)
    return build_context(
        engagement_id, t01a, message, system_desc, annex_entries,
        verification_map, verified_modality, verified_risk_tier,
        verified_sections, is_llm_or_agentic, art5_prohibited,
        art43, preview_procedure, art43_delta, pseudo_state)
