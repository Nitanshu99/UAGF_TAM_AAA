"""ScopeAgent — Tier-2 Phase 1 Declaration Verifier (§3.2 #4).

Loads the intake bundle, verifies Annex III sections and modality, enforces
the Art. 5 prohibition gate, screens for GPAI, diffs declared vs verified
values, selects the Art. 43 procedure, and writes T02–T05.

LLM path: Claude Sonnet via LiteLLM, with deterministic rule-based
verification as fallback when the LLM call fails.
"""
from __future__ import annotations

from aaa.agents.tier2.scope_agent.agent import ScopeAgent
from aaa.agents.tier2.scope_agent.errors import ScopeAgentError

__all__ = ["ScopeAgent", "ScopeAgentError"]
