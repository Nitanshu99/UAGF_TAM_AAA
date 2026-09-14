"""Scope-derived gating for the S6 (XAI) / S7 (Security) providers.

Maps the exposé's division of labour onto the audit state: S6 explains and
tests fairness/drift on the model artefact (Art. 13); S7 attacks and detects
runtime threats (Art. 15). Neither is invoked when the engagement's scope
makes their evidence meaningless — matching how the compliance-matrix module
already treats Art.13/Art.15 as *core* only at the high risk tier
(``aaa.agents.tier1.phases.compliance_matrix.logger._CORE_HIGH_RISK_ARTICLES``).
"""
from __future__ import annotations

from typing import Any


def xai_required(state: dict[str, Any]) -> tuple[bool, str]:
    """Whether S6 (explainability/fairness/drift, Art. 13) applies here.

    :param state: The audit state.
    :type state: dict[str, Any]
    :returns: ``(required, reason)`` — the reason explains either outcome.
    :rtype: tuple[bool, str]
    """
    stage_b = (state.get("client_submission") or {}).get("stage_b") or {}
    if state.get("risk_tier") != "high":
        return False, "Art. 13 is not a core requirement outside the high risk tier"
    if not stage_b.get("model_artifact_uri"):
        return False, "no evaluable model artefact was submitted"
    if not stage_b.get("task_type"):
        return False, "model artefact submitted without a declared task_type"
    if not (stage_b.get("training_dataset_uri") or stage_b.get("evaluation_dataset_uri")):
        return False, "no dataset submitted to run explainability/fairness analysis against"
    return True, "high-risk engagement with an evaluable model and dataset"


def security_required(state: dict[str, Any]) -> tuple[bool, str]:
    """Whether S7 (attack/detection, Art. 15) applies here.

    :param state: The audit state.
    :type state: dict[str, Any]
    :returns: ``(required, reason)``.
    :rtype: tuple[bool, str]
    """
    if state.get("risk_tier") == "high":
        return True, "Art. 15 is a core requirement for high-risk engagements"
    if state.get("is_llm_or_agentic"):
        return True, ("LLM/agentic systems carry a prompt-injection/runtime-detection "
                      "surface regardless of risk tier")
    return False, "Art. 15 is not in scope and the system is not LLM/agentic"
