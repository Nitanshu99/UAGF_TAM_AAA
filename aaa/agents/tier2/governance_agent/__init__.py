"""GovernanceAgent — Tier-2 Phase 5 Governance Agent (§3.2 #8).

Receives a ``Dispatch`` from the Orchestrator, pulls and validates the S4
CGSA payload, cross-checks the declared risk tier, decides Tier-3 spawns,
builds T14 (governance findings) + T15 (monitoring & logging review), and
emits a ``Report`` whose delta hydrates the §5.4 hand-off surface.

LLM path: Claude Opus via LiteLLM, with a deterministic rule-based fallback
when the LLM call fails.
"""
from __future__ import annotations

from aaa.agents.tier2.governance_agent.agent import GovernanceAgent
from aaa.agents.tier2.governance_agent.errors import GovernanceAgentError

__all__ = ["GovernanceAgent", "GovernanceAgentError"]
