"""T09, T13 and T07 claim nothing the documents or measurements do not say.

Split from test_artefacts_quote_provider_documents.py (T-20260913-100); the
grounded answers come from the provider's documents (T-20260913-032/035/041).
"""
from __future__ import annotations

from aaa.agents.tier2.model_validator.t09 import build_t09
from tests.unit.support.case06_like_dossier import STAGE_B, T01A
from tests.unit.support.provider_documents import NOW, ev


def test_t09_output_shape_comes_from_a_stated_dimension() -> None:
    """T09 output shape comes from a stated dimension."""
    found = {"output_shape": ev("A hosted model produces 128-dimensional unit vectors.",
                                 "model_card.md")}
    t09 = build_t09("eng", T01A, STAGE_B, "nlp", {}, NOW, found=found)
    assert t09["architecture"]["output_shape"] == "128-dimensional vector (model_card.md)"
    assert build_t09("eng", T01A, STAGE_B, "nlp", {}, NOW)["architecture"]["output_shape"] is None


def test_t09_does_not_invent_a_version_or_a_provider() -> None:
    """T09 does not invent a version or a provider."""
    identity = build_t09("eng", {}, STAGE_B, "nlp", {}, NOW)["model_identity"]
    assert identity["model_version"] == "not declared" and identity["provider"] is None
    assert identity["model_name"] == "not declared"


def test_t13_claims_no_examination_when_nothing_was_sampled() -> None:
    """T13 claims no examination when nothing was sampled."""
    from aaa.agents.tier2.output_fairness.context import FairnessInputs
    from aaa.agents.tier2.output_fairness.t13 import build_t13

    tox = {"sample_size": 0, "flagged_count": 0, "flagged_pct": None, "entries": [],
           "verdict": "NOT_TESTED"}
    t13 = build_t13("eng", "nlp", FairnessInputs(stage_b={}), tox, NOW,
                    "The hosted model was not accessible, so no outputs exist.")
    assert t13["sampling_narrative"].startswith("No predictions were sampled")
    assert "was not performed" in t13["art10_2f_compliance_notes"]
    assert "hosted model was not accessible" in t13["art10_2f_compliance_notes"]
    assert "inspected for discriminatory patterns" not in t13["art10_2f_compliance_notes"]


def test_t07_is_not_pass_beside_a_failing_label_bias_check() -> None:
    """T07 is not pass beside a failing label bias check."""
    from aaa.agents.tier2.data_auditor.bias import label_bias_fails

    assert label_bias_fails({"attributes": [{"attribute": "age", "four_fifths_passed": False}]})
    assert not label_bias_fails({"attributes": [{"attribute": "sex", "four_fifths_passed": True}]})
    assert not label_bias_fails(None)
