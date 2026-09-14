"""ModelValidator — Tier-2 Phase 3 Model Validation Agent (§3.2 #6).

Receives a :class:`~aaa.agents.base.Dispatch` from the Orchestrator and

1. loads T01a / T01b plus the real model and evaluation artefacts,
2. re-computes performance metrics with ``metric_suite``,
3. routes explainability to SHAP / LIME (tabular, nlp) or Grad-CAM (cv),
4. probes adversarial robustness,
5. diffs declared metrics against independent re-computation,
6. writes T09 / T10 / T11 to the Evidence Store, and
7. emits a :class:`~aaa.agents.base.Report` whose delta records the new
   artefact URIs and any HITL trigger (e.g. a robustness FAIL).

The agent is skipped for ``llm`` / ``agentic`` / ``gpai`` modalities — the
CSP routes those to UAGF-TAM-L in Group 10.

LLM path: Claude Opus via LiteLLM, with a deterministic rule-based fallback
when the LLM call fails.
"""
from __future__ import annotations

from aaa.agents.tier2.model_validator.agent import ModelValidator
from aaa.agents.tier2.model_validator.errors import ModelValidatorError

__all__ = ["ModelValidator", "ModelValidatorError"]
