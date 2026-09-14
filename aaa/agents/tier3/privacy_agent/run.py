"""Run the privacy / DPO audit, extending T08."""
from __future__ import annotations

from typing import Any

from aaa.agents.base import Dispatch, Report
from aaa.agents.tier3.confidence import spawn_confidence
from aaa.agents.tier3.privacy_agent.eval_data import load_scan_frame
from aaa.agents.tier3.privacy_agent.llm import run_llm_synthesis, with_narrative
from aaa.agents.tier3.privacy_agent.t08_update import update_t08
from aaa.agents.tier3.privacy_agent.template import T08
from aaa.platform.audit_programme import outcome
from aaa.platform.state.artefact_keys import SPAWN_PRIVACY, namespaced_key
from aaa.tools.pii_scan import pii_scan


async def run_privacy_audit(agent: Any, message: Dispatch) -> Report:
    """Run the privacy / DPO audit, extending T08.

    :param agent: The agent making the call and holding the evidence store.
    :param message: The dispatch to act on.
    :returns: The phase Report.
    """
    decl = message.get("declaration_summary", {})
    engagement_id: str = decl.get("engagement_id") or message["phase_id"]

    t08_ref = decl.get("phase_artefacts", {}).get(T08) or {}
    base_uri = t08_ref.get("uri", "") if isinstance(t08_ref, dict) else ""
    t08 = (agent.store.get_artefact(base_uri) or {}) if base_uri else {}

    # PII deep-dive: re-scan the evaluation set for leaks.
    frame, no_scan_reason = load_scan_frame(agent.store, decl)
    pii_results = ({} if frame is None
                   else pii_scan(df=frame, sample_rows=500))
    new_t08, merged_cats = update_t08(
        t08, engagement_id, pii_results, no_scan_reason)
    narrative, note = await run_llm_synthesis(agent, decl, pii_results, merged_cats)
    new_t08 = with_narrative(new_t08, narrative, note)

    t08_uri = agent.store.store_artefact(
        engagement_id, "Privacy", T08, new_t08, agent.name)
    delta = {
        # P5: a second T08 beside Phase 2's, not a replacement for it.
        "phase_artefacts": {
            namespaced_key(T08, SPAWN_PRIVACY): {
                "uri": t08_uri, "sha256": "", "template_id": T08,
                "extends": base_uri}
        },
        "privacy_tier3_triggered": False,  # already handled by this agent
        "procedure_outcomes": outcome("pii_deep_dive", not no_scan_reason, no_scan_reason),
    }
    return Report(
        phase_id="Privacy",
        artefact_uri=t08_uri,
        summary=("Privacy/DPO audit complete. "
                 + (f"Special categories detected: {len(merged_cats)}."
                    if not no_scan_reason else
                    f"The PII deep-dive did not run: {no_scan_reason}. "
                    f"Special categories carried over from Phase 2: "
                    f"{len(merged_cats)}.")),
        confidence=spawn_confidence(0.9, not no_scan_reason),
        # Fix 13's rule: a tool that did not run says so in the inventory.
        tool_calls=[{"tool": "pii_scan",
                     "result": "skipped" if no_scan_reason else "extended"}],
        declaration_verification_delta=delta,
    )


__all__ = ["run_privacy_audit"]
