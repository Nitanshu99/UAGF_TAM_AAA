"""OutputFairnessTester — Tier-2 Phase 4 Output Fairness Tester (§3.2 #7).

Receives a :class:`~aaa.agents.base.Dispatch` from the Orchestrator and

1. loads T01a / T01b plus predictions, labels and sensitive features,
2. runs the fairness suite per protected attribute — demographic parity,
   equal opportunity, disparate impact (EEOC four-fifths) and subgroup
   metrics,
3. scans a capped prediction sample for toxicity (text modalities only),
4. derives the overall fairness verdict and findings,
5. writes T12 / T13 to the Evidence Store, and
6. emits a :class:`~aaa.agents.base.Report` whose delta carries the new
   artefact URIs and any HITL trigger (fairness FAIL or discriminatory
   pattern).

The agent is skipped on the L-branch — UAGF-TAM-L owns Arts. 10 §2(f) /
15 §1 evidence for generative systems (Group 10).

LLM path: Claude Sonnet via LiteLLM, with a deterministic rule-based
fallback when the LLM call fails.
"""
from __future__ import annotations

from aaa.agents.tier2.output_fairness.agent import OutputFairnessTester
from aaa.agents.tier2.output_fairness.errors import OutputFairnessError

__all__ = ["OutputFairnessTester", "OutputFairnessError"]
