"""The Orchestrator's decide step — one ReAct observation → one decision.

Sends the summary envelope to the model behind ``load_prompt("orchestrator")``
via :meth:`BaseAgent.acompletion_json` (which routes through the active
provider and the audit log) and validates the reply into a
:class:`~aaa.agents.tier1.orchestrator.react.decisions.Decision`.
"""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.orchestrator.react.decisions import Decision, parse_decision


async def decide(agent: Any, envelope: dict[str, Any]) -> Decision:
    """Ask the Orchestrator model for the next action.

    :param agent: The :class:`Orchestrator` instance (supplies model + audit).
    :type agent: Any
    :param envelope: The per-turn summary payload from ``build_envelope``.
    :type envelope: dict[str, Any]
    :returns: The validated decision.
    :rtype: Decision
    :raises DecisionError: When the reply is not a valid decision object.
    """
    reply = await agent.acompletion_json("orchestrator", envelope)
    return parse_decision(reply)
