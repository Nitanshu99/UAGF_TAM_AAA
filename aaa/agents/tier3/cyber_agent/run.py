"""Run the cybersecurity and adversarial-robustness audit, extending T11."""
from __future__ import annotations

from typing import Any

from aaa.agents.base import Dispatch, Report
from aaa.agents.tier3.confidence import spawn_confidence
from aaa.agents.tier3.cyber_agent.delta import cyber_delta
from aaa.agents.tier3.cyber_agent.inputs import cyber_inputs
from aaa.agents.tier3.cyber_agent.llm import run_llm_synthesis, with_narrative
from aaa.agents.tier3.cyber_agent.probes import run_specialist_probes
from aaa.agents.tier3.cyber_agent.t11_update import update_t11, worst_verdict
from aaa.agents.tier3.cyber_agent.template import T11


async def run_cyber_audit(agent: Any, message: Dispatch) -> Report:
    """Run the cybersecurity and adversarial-robustness audit, extending T11.

    :param agent: The agent making the call and holding the evidence store.
    :param message: The dispatch to act on.
    :returns: The phase Report.
    """
    decl = message.get("declaration_summary", {})
    engagement_id: str = decl.get("engagement_id") or message["phase_id"]
    modality: str = (decl.get("modality") or "tabular").lower()

    t11, base_uri, probes, scored = cyber_inputs(agent, decl, engagement_id)
    injection, blocking_findings, probe_skipped, rob_verdict = run_specialist_probes(
        decl, modality, engagement_id, probes, scored)

    new_t11 = update_t11(t11, engagement_id, modality, probes, injection,
                         extended=bool(t11), probe_skipped=probe_skipped,
                         robustness=worst_verdict(t11.get("overall_robustness_verdict"), rob_verdict),
                         declared=(decl.get("stage_b") or {}).get("robustness_metrics"))
    narrative, note = await run_llm_synthesis(
        agent, decl, probes, injection, blocking_findings)
    new_t11 = with_narrative(new_t11, narrative, note)

    t11_uri = agent.store.store_artefact(
        engagement_id, "CyberSecurity", T11, new_t11, agent.name)
    delta = cyber_delta(t11_uri, base_uri, blocking_findings, probe_skipped,
                        new_t11.get("skipped_reason"))
    return Report(
        phase_id="Cyber",
        artefact_uri=t11_uri,
        summary=(f"CyberSecurity audit complete. Probes run: {len(probes)}. "
                 f"Blocking findings: {len(blocking_findings)}. "
                 + ("Extends the Phase 3 T11." if t11 else
                    "No Phase 3 T11 was available to extend; this report covers "
                    "the specialist probes only.")),
        confidence=spawn_confidence(0.85, not probe_skipped),
        # Fix 13's rule: a tool that did not run says so in the inventory.
        tool_calls=[{"tool": "robustness_probe",
                     "result": "skipped" if probe_skipped else "extended"}],
        declaration_verification_delta=delta,
    )


__all__ = ["run_cyber_audit"]
