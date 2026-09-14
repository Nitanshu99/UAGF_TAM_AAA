"""CyberSecurityAgent — Tier-3 independent security review (§3.3).

Runs deeper adversarial-robustness probes than Phase 3, plus prompt-injection
and sandbox-escape probes for generative systems.  Extends
T11_robustness_report and may emit blocking findings.

LLM path: Claude Sonnet via LiteLLM, with a deterministic rule-based fallback.
"""
from __future__ import annotations

from aaa.agents.tier3.cyber_agent.agent import CyberSecurityAgent

__all__ = ["CyberSecurityAgent"]
