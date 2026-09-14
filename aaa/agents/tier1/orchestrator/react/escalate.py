"""Finding F8 — what ``ESCALATE_HITL`` actually does.

PROMPT.md §Agent 1 ordered the Orchestrator to "pause the audit and emit a HITL
alert". Two things were wrong with that. The vocabulary had no token for it, so
the model emitted no-op ``PLAN``s while narrating "Audit remains paused"; and
the runtime has not paused on HITL since the provisional-report rework —
``node_hitl_checkpoint`` continues to Phase 6 and the engagement closes with a
provisional report plus a review packet resolved later by
``scripts/finalize_hitl.py``.

So the action records the alert and sequencing continues. It lands in two places:
``hitl_reason``, which the T18 report front matter already renders, and the
append-only ``hitl_alerts``. The second exists because ``hitl_reason`` is a
single string that roughly a dozen writers assign to — the very next phase to
close ``escalate_hitl`` overwrites it (``verification.finish_phase``) — so an
Orchestrator alert kept only there would routinely be erased before anyone read
it. ``hitl_alerts`` is what the HITL review packet reports.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_REASON = "Orchestrator escalated the engagement for human review."


def record_escalation(state: dict[str, Any], rationale: str) -> dict[str, Any]:
    """Record an Orchestrator-raised HITL alert on *state* and carry on.

    The model's ``rationale`` is the alert text a reviewer reads, so it is kept
    verbatim and appended to any reason a phase already recorded rather than
    overwriting it — an engagement can be escalated for more than one thing.

    :param state: The mutable AuditState dict.
    :type state: dict[str, Any]
    :param rationale: The decision's one-line rationale.
    :type rationale: str
    :returns: The same state, flagged for human review.
    :rtype: dict[str, Any]
    """
    alert = (rationale or "").strip() or _DEFAULT_REASON
    already = bool(state.get("hitl_required"))
    alerts: list[str] = state.setdefault("hitl_alerts", [])
    if alert not in alerts:
        alerts.append(alert)
    prior = (state.get("hitl_reason") or "").strip()
    if prior and alert not in prior:
        state["hitl_reason"] = f"{prior} | Orchestrator: {alert}"
    elif not prior:
        state["hitl_reason"] = f"Orchestrator: {alert}"
    state["hitl_required"] = True
    logger.warning(
        "ReAct: Orchestrator escalated to HITL (%s) — %s; the audit continues to a "
        "provisional report and a review packet.",
        "already flagged" if already else "newly flagged", alert)
    return state


__all__ = ["record_escalation"]
