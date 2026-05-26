"""
model_registry — per-agent model + OpenAI service-tier assignment.

Single source of truth that maps every agent in the 12-agent roster to:

* ``model``        — LiteLLM model string (resolved by ``litellm.acompletion``).
* ``service_tier`` — optional OpenAI processing tier.  Non-interactive agents
  (Verifier, ModelValidator, GovernanceAgent, ReportArchitect, UAGF-TAM-L)
  opt into ``"flex"`` to claim the 50 % discount.  Interactive / critical-path
  agents stay on the default tier so a ``429 Resource Unavailable`` from
  spare-capacity exhaustion cannot stall the audit head.

The registry is keyed by ``BaseAgent.name`` exactly as set in each agent
constructor (``super().__init__(name="Verifier", …)``) so agents can resolve
their config with ``get_model_config(self.name)`` without string drift.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ModelConfig:
    """Resolved model + optional service tier for a single agent."""

    model: str
    service_tier: str | None = None

    def litellm_kwargs(self) -> dict[str, Any]:
        """Return kwargs suitable for ``litellm.acompletion(**kwargs, …)``.

        Includes ``service_tier`` only when set, so non-OpenAI providers
        invoked with a fallback model are not handed an unknown param.
        """
        kw: dict[str, Any] = {"model": self.model}
        if self.service_tier is not None:
            kw["service_tier"] = self.service_tier
        return kw


# Agents that benefit from Flex Processing: long-running, non-interactive
# critique / synthesis steps where the 50 % discount outweighs the higher
# latency and 429-on-peak-capacity risk.
FLEX_AGENTS: frozenset[str] = frozenset({
    "Verifier",
    "ModelValidator",
    "GovernanceAgent",
    "ReportArchitect",
    "UAGF-TAM-L",
})


# Per-agent registry.  Keys MUST match ``BaseAgent.name`` strings.
AGENT_MODELS: dict[str, ModelConfig] = {
    # 1. Orchestrator — high-reasoning planner, short prompts, on critical path.
    "Orchestrator":         ModelConfig("gpt-5.5"),
    # 2. Verifier — critical critique over all artefacts (Flex).
    "Verifier":             ModelConfig("gpt-5.5", service_tier="flex"),
    # 3. Regulatory RAG — top-K chunk QA, short prompts.
    "Regulatory RAG":       ModelConfig("gpt-5.4-nano"),
    # 4. Phase 1 — Annex III classification.
    "ScopeAgent":           ModelConfig("gpt-5.4"),
    # 5. Phase 2 — Dataset lineage / governance, long context.
    "DataAuditor":          ModelConfig("gpt-5.4"),
    # 6. Phase 3 — Model validation + evals (Flex).
    "ModelValidator":       ModelConfig("gpt-5.5", service_tier="flex"),
    # 7. Phase 4 — Bounded fairness interpretation, short prompts.
    "OutputFairnessTester": ModelConfig("gpt-5.4-mini"),
    # 8. Phase 5 — CGSA ingest + Art. 9 chain (Flex).
    "GovernanceAgent":      ModelConfig("gpt-5.5", service_tier="flex"),
    # 9. Phase 6 — Assembles all artefacts (Flex).
    "ReportArchitect":      ModelConfig("gpt-5.4", service_tier="flex"),
    # 10. UAGF-TAM-L — RAGAs + trajectory audit (Flex).
    "UAGF-TAM-L":           ModelConfig("gpt-5.5", service_tier="flex"),
    # 11. Cybersecurity — targeted Art. 15 evidence.
    "CyberSecurityAgent":   ModelConfig("gpt-5.4"),
    # 12. Privacy / DPO — GDPR overlap check.
    "PrivacyDPOAgent":      ModelConfig("gpt-5.4"),
}


def get_model_config(agent_name: str) -> ModelConfig:
    """Return :class:`ModelConfig` for *agent_name*.

    Raises :class:`KeyError` if the agent is not registered — surfacing typos
    at construction time rather than at the first LLM call.
    """
    return AGENT_MODELS[agent_name]


def resolve_model(agent_name: str, override: str | None = None) -> str:
    """Return *override* if non-empty, else the registry model for *agent_name*."""
    if override:
        return override
    return AGENT_MODELS[agent_name].model


def resolve_service_tier(
    agent_name: str, override: str | None = None
) -> str | None:
    """Return *override* if provided, else the registry service tier."""
    if override is not None:
        return override
    return AGENT_MODELS[agent_name].service_tier


__all__ = [
    "AGENT_MODELS",
    "FLEX_AGENTS",
    "ModelConfig",
    "get_model_config",
    "resolve_model",
    "resolve_service_tier",
]
