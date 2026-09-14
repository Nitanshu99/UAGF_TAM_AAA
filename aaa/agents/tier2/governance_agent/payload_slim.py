"""Drop the handoff fields the state delta already carries, enriched (M6).

Fix F2 removed the *nested* second copy of ``cgsa_payload``, halving the Phase 5
prompt. What it left is smaller and subtler: ``aaa_phase5_handoff`` carries
``blocking_findings``, ``low_confidence_controls``, ``positive_findings``,
``aaa_recommended_follow_up`` and ``phase5_narrative_summary``, and
``ingest_state_delta`` carries every one of them again — as a strict superset,
each finding joined to its control name, its remediation action and the full
``eu_ai_act_articles`` list that fix F19 exists to preserve.

So the model reads each blocking finding twice, the second time in a form that
answers questions the first cannot. Verified against the assessed payload of
call #052: 32 blocking findings and 24 low-confidence controls, every raw entry
key-for-key inside its enriched counterpart, 14,696 characters — 6.8 % of that
user message.

Only demonstrably-contained fields go. The rest of the handoff stays: nothing
else in it is restated anywhere (``annex_iv_completeness``, ``critical_gaps``,
``high_gaps``, ``s5_integration_note``), and ``remediation_roadmap`` stays in
full because the delta's normalisation of it is *lossy* — it drops
``control_name``, ``eu_ai_act_article``, ``current_score``/``target_score`` and
``effort_estimate``, so the two are not the same evidence.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

#: Handoff fields ``ingest_state_delta`` restates in enriched form.
_RESTATED = ("blocking_findings", "low_confidence_controls", "positive_findings",
             "aaa_recommended_follow_up", "phase5_narrative_summary")


def slim_cgsa_payload(payload: Any) -> Any:
    """Return *payload* without the handoff fields the delta already carries.

    :param payload: The CGSA assessment as ingested.
    :returns: A copy with the restated handoff fields replaced by a pointer, or
        *payload* unchanged when it has no handoff block.
    """
    handoff = payload.get("aaa_phase5_handoff") if isinstance(payload, dict) else None
    if not isinstance(handoff, dict):
        return payload
    slimmed = deepcopy(payload)
    dropped = [key for key in _RESTATED if key in slimmed["aaa_phase5_handoff"]]
    for key in dropped:
        del slimmed["aaa_phase5_handoff"][key]
    if dropped:
        slimmed["aaa_phase5_handoff"]["_moved"] = (
            "The fields " + ", ".join(dropped) + " are in `ingest_state_delta` "
            "as cgsa_* keys, each entry joined to its control name, remediation "
            "action and full eu_ai_act_articles list. Read them there.")
    return slimmed


__all__ = ["slim_cgsa_payload"]
