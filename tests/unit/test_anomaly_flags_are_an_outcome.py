"""An anomaly detector is not exempt from group fairness by its model type (T-20260914-040, case 03)."""
from __future__ import annotations

from aaa.agents.tier2.output_fairness import skip_cause
from aaa.agents.tier2.output_fairness.articles import EVIDENCED_ARTICLES
from aaa.agents.tier2.output_fairness.context import FairnessInputs, SuiteResult
from aaa.agents.tier2.output_fairness.verdicts import apply_verdict_findings


def test_an_anomaly_model_without_protected_attributes_is_an_evidence_gap() -> None:
    """Case 03: sensitive_feature_columns is empty — the gap is the declaration, not the model."""
    inp = FairnessInputs(stage_b={}, task_type="anomaly",
                         skip_cause=skip_cause.NO_PROTECTED_ATTRIBUTES,
                         skip_detail={"declared_attributes": []})
    suite = SuiteResult(per_attribute=[], sample_size=None, dp={}, eo={}, di={}, sg={},
                        overall_verdict="NOT_TESTED")
    reason = apply_verdict_findings(inp, suite) or ""
    assert suite.overall_verdict == "NOT_TESTED"
    assert [(f["finding_id"], f["materiality"]) for f in inp.findings] == [
        ("P4-NOT-TESTED", "possibly_material")]
    assert "no groups whose outcome rates could be compared" in reason
    assert "none declared" in reason
    assert "document why its outputs affect no group of persons" in inp.findings[0]["recommendation"]
    assert inp.insufficient == set(EVIDENCED_ARTICLES)
