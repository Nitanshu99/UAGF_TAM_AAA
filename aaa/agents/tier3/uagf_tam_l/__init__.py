"""UagfTamLBranch — Tier-3 Agent for LLM/agentic/GPAI systems (§3.3 #10).

Replaces Phases 2–4 for generative modalities: golden-set evaluation, RAGAs
metrics, groundedness, prompt-injection red-teaming, and (for agentic
systems) trajectory audit.  Emits T16_uagf_tam_l_evidence.

LLM path: Claude Opus via LiteLLM, with deterministic rule-based fallbacks
inside each tool.
"""
from __future__ import annotations

from aaa.agents.tier3.uagf_tam_l.agent import UagfTamLBranch

__all__ = ["UagfTamLBranch"]
