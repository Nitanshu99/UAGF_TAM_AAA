"""model_registry — per-agent model + OpenAI service-tier assignment.

Single source of truth that maps every agent in the 14-agent roster to:

* ``model``        — LiteLLM model string (resolved by ``litellm.acompletion``).
* ``service_tier`` — optional OpenAI processing tier.  Non-interactive agents
  (Verifier, ModelValidator, GovernanceAgent, ReportArchitect, UAGF-TAM-L)
  opt into ``"flex"`` to claim the 50 % discount.  Interactive / critical-path
  agents stay on the default tier so a ``429 Resource Unavailable`` from
  spare-capacity exhaustion cannot stall the audit head.

The registry is keyed by ``BaseAgent.name`` exactly as set in each agent
constructor (``super().__init__(name="Verifier", …)``) so agents can resolve
their config with ``get_model_config(self.name)`` without string drift."""
from aaa.platform.model_registry.flex_disabled import (  # noqa: F401
    _flex_disabled,
    resolve_service_tier,
)
from aaa.platform.model_registry.model_config import ModelConfig  # noqa: F401
from aaa.platform.model_registry.nvidia_roster import NVIDIA_AGENT_MODELS  # noqa: F401
from aaa.platform.model_registry.provider import active_provider  # noqa: F401
from aaa.platform.model_registry.resolve import get_model_config, resolve_model  # noqa: F401
from aaa.platform.model_registry.roster import AGENT_MODELS, FLEX_AGENTS  # noqa: F401

__all__ = [
    'ModelConfig',
    'FLEX_AGENTS',
    'AGENT_MODELS',
    'NVIDIA_AGENT_MODELS',
    'get_model_config',
    'resolve_model',
    'active_provider',
    '_flex_disabled',
    'resolve_service_tier',
]
