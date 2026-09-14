"""T-20260913-107: a classifier's labels are not screened for language, nor claimed inspected.

Case 05's toxicity screen read the CV screener's "0"/"1" decisions, found nothing,
and T13 said the outputs were inspected for discriminatory patterns.
"""
from __future__ import annotations

from aaa.agents.tier2.output_fairness.context import FairnessInputs
from aaa.agents.tier2.output_fairness.t13 import build_t13
from aaa.agents.tier2.output_fairness.toxicity import outputs_are_text, run_toxicity
from aaa.platform.evidence.contract import artefact_schema_errors

_NOW = "2026-09-13T00:00:00Z"


def _screener() -> FairnessInputs:
    return FairnessInputs(stage_b={}, y_true=[0, 1, 1, 0] * 20, y_pred=[0, 1, 0, 0] * 20,
                          prediction_ids=list(range(80)), task_type="classification")


def test_label_outputs_are_not_screened_and_nothing_is_claimed() -> None:
    """NOT_TESTED, a null pattern flag, and a note that points at T12."""
    inp = _screener()
    tox = run_toxicity(inp, "nlp")
    assert tox["verdict"] == "NOT_TESTED" and not tox["entries"]
    t13 = build_t13("eng", "nlp", inp, tox, _NOW)
    assert t13["discriminatory_pattern_detected"] is None and t13["hitl_review_required"] is False
    assert "group-fairness analysis recorded in T12" in t13["art10_2f_compliance_notes"]
    assert "inspected for discriminatory patterns" not in t13["art10_2f_compliance_notes"]
    assert not artefact_schema_errors("T13_output_sampling_log", t13)


def test_generated_language_is_still_screened() -> None:
    """Supplied texts, or text outputs outside the label space, are language."""
    replies = FairnessInputs(stage_b={}, y_true=[0, 1], task_type="unknown",
                             y_pred=["We will not hire you.", "Welcome aboard."])
    assert outputs_are_text(replies, "llm")
    assert outputs_are_text(FairnessInputs(stage_b={}, prediction_texts=["a reply"]), "tabular")
    assert not outputs_are_text(FairnessInputs(stage_b={}, y_true=["yes", "no"],
                                               y_pred=["no", "yes"]), "nlp")
