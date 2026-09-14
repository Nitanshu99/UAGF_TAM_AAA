"""DataAuditor — Tier-2 Phase 2 Data Governance Auditor (§3.2 #5).

Loads the real training/evaluation dataset, runs profiling, missingness,
class-balance, and PII scans, derives an evidence-grounded quality verdict,
and emits T06 (datasheet), T07 (data quality report), and T08
(special-category data log).  Undeclared special-category data raises a
material finding and triggers the Privacy Tier-3 spawn.

LLM path: Claude Sonnet via LiteLLM, with a deterministic rule-based
fallback when the LLM call fails.
"""
from __future__ import annotations

from aaa.agents.tier2.data_auditor.agent import DataAuditor
from aaa.agents.tier2.data_auditor.errors import DataAuditorError

__all__ = ["DataAuditor", "DataAuditorError"]
