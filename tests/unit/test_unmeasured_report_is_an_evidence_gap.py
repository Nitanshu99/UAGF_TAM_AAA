"""Provider issues on a report that measured nothing are gaps; ranking metrics are a procedure (T-043/044/045)."""
from __future__ import annotations

from aaa.agents.tier1.phases.verification.provider_findings.unmeasured import as_measured
from aaa.agents.tier2.model_validator.context import Explainability
from aaa.agents.tier2.model_validator.t10 import build_t10
from aaa.platform.audit_programme.apply import apply_audit_programme
from aaa.platform.audit_programme.procedures import outcome

_ISSUE = {"issue_type": "provider_nonconformity", "materiality": "material",
          "description": "No probes executed for a high-risk system under Art. 15."}


def test_a_non_conformity_on_an_unperformed_probe_becomes_a_gap() -> None:
    """Case 06: the probe had no model, so T11 cannot evidence a breach."""
    state = {"procedure_outcomes": outcome("robustness_probe", False, "No model.predict supplied.")}
    issue = as_measured(_ISSUE, "T11_robustness_report", state)
    assert issue["issue_type"] == "evidence_gap"
    assert "No model.predict supplied." in issue["description"]


def test_a_performed_probe_or_another_template_is_left_alone() -> None:
    """A measured T11 can carry a non-conformity; T16's documentation findings are untouched."""
    performed = {"procedure_outcomes": outcome("robustness_probe", True)}
    assert as_measured(_ISSUE, "T11_robustness_report", performed) is _ISSUE
    unperformed = {"procedure_outcomes": outcome("robustness_probe", False, "none")}
    assert as_measured(_ISSUE, "T16_uagf_tam_l_evidence", unperformed) is _ISSUE


def test_recomputed_ranking_metrics_evidence_accuracy() -> None:
    """Case 06: metric_suite could not run, the ranking recomputation did."""
    state = {"procedure_outcomes": {**outcome("metric_suite", False, "no predictions"),
                                    **outcome("ranking_metrics", True)}}
    limitations = apply_audit_programme(state)
    assert "Art.15" not in state["insufficient_evidence_articles"]
    assert [x["effect"] for x in limitations] == ["disclosed"]


def test_t10_says_no_technique_ran() -> None:
    """Not "techniques applied: ['none']"."""
    expl = Explainability(techniques=["none"], global_expl={}, local_expl=[], visual_expl=[])
    note = build_t10("eng-06", "nlp", expl, "2026-09-14T00:00:00Z")["art13_compliance_notes"]
    assert "['none']" not in note and "No explainability technique was applied" in note


def test_a_non_conformity_on_untested_output_fairness_becomes_a_gap() -> None:
    """T-20260914-063: case 06's CLI Verifier failed Art.10§2(f) on T13 with nothing sampled."""
    not_tested = {"finding_id": "P4-NOT-TESTED", "materiality": "possibly_material",
                  "description": "Output fairness could not be tested. Model predictions unavailable."}
    state = {"blocking_findings": [not_tested]}
    for tid in ("T13_output_sampling_log", "T12_output_fairness_report"):
        issue = as_measured(_ISSUE, tid, state)
        assert issue["issue_type"] == "evidence_gap"
        assert "P4-NOT-TESTED records that nothing was measured" in issue["description"]


def test_tested_output_fairness_keeps_its_non_conformity() -> None:
    """With no P4-NOT-TESTED, Phase 4 measured something and a non-conformity can stand."""
    state = {"blocking_findings": [{"finding_id": "P4-FAIR-SEX", "materiality": "material"}]}
    assert as_measured(_ISSUE, "T13_output_sampling_log", state) is _ISSUE
    assert as_measured(_ISSUE, "T11_robustness_report", state) is _ISSUE
