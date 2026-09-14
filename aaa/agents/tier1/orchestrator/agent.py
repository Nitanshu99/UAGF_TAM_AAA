"""The Orchestrator class — thin coordinator over graph and phase modules."""
from __future__ import annotations

import logging
import uuid
from typing import Any

from aaa.agents.base import BaseAgent
from aaa.agents.tier1.agent_initializer import initialise_agents, unwired_agents
from aaa.agents.tier1.checkpointer import make_checkpointer
from aaa.agents.tier1.orchestrator import runner
from aaa.agents.tier1.orchestrator.graph import build_graph
from aaa.agents.tier1.phases.initial_state import build_initial_state
from aaa.agents.tier1.verifier import Verifier
from aaa.platform.model_registry import resolve_model, resolve_service_tier
from aaa.platform.model_registry.timeouts import resolve_timeout

logger = logging.getLogger(__name__)


class Orchestrator(BaseAgent):
    """Lead orchestrator — delegates to :mod:`aaa.agents.tier1.phases`.

    :param model: Optional LLM model override.
    :param evidence_store: Optional EvidenceStore; enables real phase agents.
    :param regulatory_rag: RegulatoryRAG passed to the phase agents and
        to the Verifier, which resolves the citations it judges (F14).
    :param service_tier: Optional OpenAI service tier override.
    """

    def __init__(self, model: str | None = None, evidence_store: Any = None,
                 regulatory_rag: Any = None, service_tier: str | None = None):
        super().__init__(
            name="Orchestrator",
            model=resolve_model("Orchestrator", model),
            service_tier=resolve_service_tier("Orchestrator", service_tier),
            # The decide loop runs outside any phase deadline, so fix 37's rule
            # does not reach it and it took the 120 s default while its calls ran
            # to 303.7 s — which only worked while fix 46's tripling hid it.
            timeout=resolve_timeout("Orchestrator"),
        )
        self._verifier = Verifier(regulatory_rag=regulatory_rag)
        self._checkpointer = make_checkpointer()
        self._evidence_store = evidence_store
        # All phase agents loaded via initialise_agents (fails gracefully per agent)
        self._agents: dict[str, Any] = initialise_agents(
            evidence_store=evidence_store, regulatory_rag=regulatory_rag)
        # F4 (S3): which agents are missing is a property of *this run*, and the
        # deliverable has to carry it — a log line the runner never wrote is how
        # an unwired ScopeAgent reached S6 as a schema complaint.
        self._unwired: list[str] = unwired_agents(self._agents)
        self._graph = self._build_graph()

    def _build_graph(self, checkpointer: Any | None = None) -> Any:
        """Compile the StateGraph bound to this instance's agents."""
        return build_graph(self._agents, checkpointer)

    async def process(self, message: dict) -> dict:  # type: ignore[override]
        """Run a full engagement audit.

        :param message: ``{engagement_id, client_submission}``.
        :returns: Final AuditState dict.
        """
        engagement_id = message.get("engagement_id") or str(uuid.uuid4())
        state = build_initial_state(engagement_id, message.get("client_submission", {}))
        return await self.run(state)

    run = runner.run
    _run_langgraph = runner._run_langgraph
