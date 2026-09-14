"""PrivacyDPOAgent — Tier-3 privacy / DPO review (§3.3).

Runs a deep-dive PII scan over the evaluation set, merges detected special
categories into T08, and cross-references DPIA obligations (GDPR Art. 9 /
EU AI Act Art. 10 §5).

LLM path: Claude Sonnet via LiteLLM, with a deterministic rule-based fallback.
"""
from __future__ import annotations

from aaa.agents.tier3.privacy_agent.agent import PrivacyDPOAgent

__all__ = ["PrivacyDPOAgent"]
