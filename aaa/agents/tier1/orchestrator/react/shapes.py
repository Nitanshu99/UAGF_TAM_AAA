"""Tolerance for the reply shapes models emit around the decision contract.

PROMPT.md §Agent 1 mandates one decision object per reply, but models still
occasionally wrap it (``decision_sequence``), reach for the Dispatch envelope
the prompt documented before the ReAct rewrite, or name a tool instead of an
action. The prompt no longer shows any of those shapes; the tolerance stays
because a model may still produce them. Normalising here keeps
a substantively-correct decision from being discarded — a rejected decision
drops the audit into deterministic sequencing, which is the outcome this whole
design exists to avoid.
"""
from __future__ import annotations

import re
from typing import Any

#: keys a model may wrap its decision in despite the one-decision contract.
_WRAPPERS = ("decision_sequence", "decisions", "steps", "plan", "actions")

#: PROMPT.md names csp_solver as the PLAN tool, so a reply reaching for it is
#: unambiguously a PLAN turn.
_TOOL_ACTIONS = {"run_csp_solver": "PLAN", "csp_solver": "PLAN"}

#: Phrasings for the HITL escalation. The prompt ordered "pause the audit and
#: emit a HITL alert" until fix 4 replaced it with the ``ESCALATE_HITL`` token,
#: so a model reaching for that behaviour may still reach for these words rather
#: than for the contract token — and a rejected decision costs the audit its
#: LLM-driven sequencing.
_ACTION_ALIASES = {
    "HITL": "ESCALATE_HITL",
    "ESCALATE": "ESCALATE_HITL",
    "ESCALATE_TO_HITL": "ESCALATE_HITL",
    "HITL_ALERT": "ESCALATE_HITL",
    "HITL_ESCALATION": "ESCALATE_HITL",
    "PAUSE": "ESCALATE_HITL",
    "PAUSE_AUDIT": "ESCALATE_HITL",
}


def unwrap(payload: Any) -> Any:
    """Unwrap a single-decision list emitted despite the one-decision contract.

    :param payload: Parsed JSON reply from the Orchestrator model.
    :type payload: Any
    :returns: The inner decision object, or *payload* unchanged.
    :rtype: Any
    """
    if isinstance(payload, list) and payload:
        return payload[0]
    if isinstance(payload, dict):
        for key in _WRAPPERS:
            inner = payload.get(key)
            if isinstance(inner, list) and inner:
                return inner[0]
            if isinstance(inner, dict):
                return inner
    return payload


def action_of(payload: dict[str, Any]) -> str:
    """Read the action, accepting the Dispatch envelope and tool names.

    :param payload: Unwrapped decision object.
    :type payload: dict[str, Any]
    :returns: Upper-cased action name; ``""`` when none can be determined.
    :rtype: str
    """
    action = str(payload.get("action", "")).strip().upper().replace(" ", "_")
    if action:
        return _ACTION_ALIASES.get(action, action)
    if str(payload.get("message_type", "")).strip().lower() == "dispatch":
        return "DISPATCH"
    step = str(payload.get("step") or payload.get("tool") or "").strip().lower()
    return _TOOL_ACTIONS.get(step, "")


def normalise_phase(raw: Any) -> str:
    """Normalise a model-supplied phase id onto the canonical tokens.

    :param raw: The model's ``phase_id`` value (e.g. ``"P4_Output"``).
    :type raw: Any
    :returns: Canonical phase id, or the cleaned token when no match exists.
    :rtype: str
    """
    token = str(raw or "").strip().upper().replace("PHASE", "P").replace(" ", "")
    match = re.match(r"^P?_?([1-6])", token)
    if match:
        return f"P{match.group(1)}"
    for branch in ("CYBER", "PRIVACY"):
        if token.startswith(branch[:4]):
            return branch
    return "L" if token.startswith("L") else token
