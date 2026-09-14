"""Run the UAGF-TAM L-branch evaluation and file T16."""
from __future__ import annotations

from typing import Any

from aaa.agents.base import Dispatch, Report
from aaa.agents.tier3.confidence import spawn_confidence
from aaa.agents.tier3.uagf_tam_l.gather import gather_t16
from aaa.agents.tier3.uagf_tam_l.injection import _injection_result, _rate
from aaa.agents.tier3.uagf_tam_l.llm import run_llm_synthesis, with_narrative
from aaa.agents.tier3.uagf_tam_l.procedures import l_branch_outcomes


async def run_uagf_tam_l_branch(agent: Any, message: Dispatch) -> Report:
    """Run the UAGF-TAM L-branch evaluation and file T16.

    :param agent: The agent making the call and holding the evidence store.
    :param message: The dispatch to act on.
    :returns: The phase Report.
    """
    decl = message.get("declaration_summary", {})
    engagement_id: str = decl.get("engagement_id") or message["phase_id"]
    modality: str = (decl.get("modality") or "llm").lower()

    t16 = await gather_t16(agent, decl, engagement_id, modality)
    t16 = with_narrative(t16, *await run_llm_synthesis(agent, decl, t16))
    golden_set, injection_results = t16["golden_set_results"], t16["prompt_injection_results"]
    t16_uri = agent.store.store_artefact(
        engagement_id, "phase_L", "T16_uagf_tam_l_evidence", t16, agent.name)
    delta = {"phase_artefacts": {"T16_uagf_tam_l_evidence": {
        "uri": t16_uri, "sha256": "", "template_id": "T16_uagf_tam_l_evidence"}},
        "procedure_outcomes": l_branch_outcomes(golden_set, injection_results)}
    return Report(
        phase_id="PL",
        artefact_uri=t16_uri,
        summary=(f"UAGF-TAM-L audit complete. Pass rate={_rate(golden_set)}. "
                 f"Verdict={t16['overall_verdict']}."),
        confidence=spawn_confidence(0.9, bool(golden_set.get("scored"))
                                    or injection_results.get("vulnerability_rate") is not None),
        tool_calls=[
            # Was "computed" on every run, including the ones that scored nothing.
            {"tool": "ragas_eval", "result": ("computed" if golden_set.get("scored") else
                                              f"not scored: {golden_set.get('unscored_reason')}")},
            {"tool": "prompt_injection_suite",
             "result": _injection_result(injection_results)},
        ],
        declaration_verification_delta=delta,
    )


__all__ = ["run_uagf_tam_l_branch"]
