"""nvidia_roster.py — NVIDIA NIM (build.nvidia.com) mirror of ``AGENT_MODELS``.

Selected via ``PROVIDER=nvidia`` (see
:mod:`aaa.platform.model_registry.provider`). No agent carries a
``service_tier``: NIM's OpenAI-compatible endpoint does not support OpenAI's
Flex processing tier.

Single-model roster (2026-08-15). The previous three-tier split
(deepseek-v4-pro / deepseek-v4-flash / nemotron-3-nano) collapsed when both
DeepSeek models reached end of life on 2026-08-07 and began returning HTTP 410
Gone, silently falling every agent back to its deterministic path. Note which
identifier survived: ``deepseek-v4-flash`` was withdrawn while the dated
snapshot ``deepseek-v4-flash-0731`` stayed live — the same unpinned-alias
failure the Stage B provenance contract now requires customers to avoid.

Nemotron 3 Ultra is a 550B-parameter Latent-MoE model with 55B active
parameters, built for reasoning, tool use and agentic tasks. Applying it to
every agent trades throughput for uniform quality: reasoning is on by default,
which costs roughly 3-4x the output tokens and an order of magnitude more
latency per call than the same model with thinking disabled. That is a
deliberate choice — quality over speed on a free-tier account — not an
oversight.
"""
from __future__ import annotations

from aaa.platform.model_registry.model_config import ModelConfig

#: Context window declared for the NIM deployment. NVIDIA publishes "up to 1M
#: tokens" for the Nemotron 3 family, but their own serving configuration
#: defaults to 262144 and requires an explicit opt-in flag to exceed it. The
#: served default is the honest figure for the token guard; claiming 1M here
#: would size budgets against capacity this endpoint does not offer.
_CONTEXT_WINDOW = 262144

#: One model for the whole roster (user decision, 2026-08-15).
_ULTRA = ModelConfig("nvidia_nim/nvidia/nemotron-3-ultra-550b-a55b",
                     context_window=_CONTEXT_WINDOW)

NVIDIA_AGENT_MODELS: dict[str, ModelConfig] = {
    "Orchestrator":         _ULTRA,
    "Verifier":             _ULTRA,
    "Regulatory RAG":       _ULTRA,
    "ScopeAgent":           _ULTRA,
    "DataAuditor":          _ULTRA,
    "ModelValidator":       _ULTRA,
    "OutputFairnessTester": _ULTRA,
    "GovernanceAgent":      _ULTRA,
    "ReportArchitect":      _ULTRA,
    "UAGF-TAM-L":           _ULTRA,
    "CyberSecurityAgent":   _ULTRA,
    "PrivacyDPOAgent":      _ULTRA,
    "DocIntelligenceAgent": _ULTRA,
    "ClientBrief":          _ULTRA,
}
