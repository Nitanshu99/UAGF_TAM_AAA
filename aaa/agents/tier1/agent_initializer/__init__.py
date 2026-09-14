"""
aaa.agents.tier1.agent_initializer — Lazy agent instantiation for the Orchestrator.

Provides ``initialise_agents(evidence_store, regulatory_rag)`` which attempts
to import and construct every phase agent, logging a warning on failure so that
the Orchestrator always starts (falling back to stubs).

Fix F4 (finding S3) made that failure *findable*. An agent that fails to
construct is left ``None``, and a ``None`` agent makes its phase runner write
deterministic placeholders — so an unwired ScopeAgent is why the 2026-09-03
finclear delivery reached S6 with ``annex_iii_mapping: []``. The only record of
the cause was one ``logger.warning`` carrying no traceback, sent to a logger the
mock-case runner does not write to: ``logs/agents/agents.log`` holds **zero**
``Could not instantiate`` lines for that run. Diagnosing it meant reading an
assessment document written days later.

Three changes, all cheap. The per-agent failure logs at ERROR with its traceback.
The set of unwired agents is logged once, explicitly, as its own line — the fact
a reader needs is *which agents are missing*, not *n separate exceptions*. And
:func:`unwired_agents` exposes that set to the caller, so it reaches
``run_integrity`` and travels with the deliverable rather than living only in a
log file that may not exist.
"""
from __future__ import annotations

import logging
from typing import Any

from aaa.agents.tier1.agent_initializer.specs import _AGENT_SPECS, import_class

logger = logging.getLogger(__name__)

def unwired_agents(agents: dict[str, Any]) -> list[str]:
    """Names in *agents* that hold no agent, so their phase will be stubbed.

    :param agents: The registry returned by :func:`initialise_agents`.
    :returns: Sorted attribute names whose agent is ``None``.
    """
    return sorted(name for name, agent in agents.items() if agent is None)


def initialise_agents(
    evidence_store: Any,
    regulatory_rag: Any = None,
) -> dict[str, Any]:
    """Attempt to construct all phase agents.  Returns attr_name → agent dict."""
    agents: dict[str, Any] = {attr: None for attr, _, _ in _AGENT_SPECS}

    if evidence_store is None:
        # Not a per-agent failure but the whole pipeline: every phase will stub.
        # Legitimate in a unit test; catastrophic and silent in a real run.
        logger.error(
            "No evidence store supplied — ALL %d phase agents will be unwired and "
            "every phase will deliver placeholders. This run cannot produce evidence.",
            len(agents))
        return agents

    for attr_name, class_path, extra in _AGENT_SPECS:
        try:
            cls = import_class(class_path)
            kwargs: dict[str, Any] = {"evidence_store": evidence_store}
            if "regulatory_rag" in extra:
                kwargs["regulatory_rag"] = regulatory_rag
            agents[attr_name] = cls(**kwargs)
        except Exception as exc:  # pragma: no cover
            # exc_info: the message alone cost a later reader the actual cause.
            logger.error(
                "Could not instantiate %s: %s; %s will be STUBBED and its artefacts "
                "will be placeholders.", class_path, exc, attr_name, exc_info=True)

    missing = unwired_agents(agents)
    if missing:
        logger.error(
            "Unwired agents (%d of %d): %s. The phases they own will deliver "
            "placeholder artefacts; the run is DEGRADED and must not be handed off.",
            len(missing), len(agents), ", ".join(missing))
    return agents


__all__ = ["_AGENT_SPECS", "initialise_agents", "unwired_agents"]
