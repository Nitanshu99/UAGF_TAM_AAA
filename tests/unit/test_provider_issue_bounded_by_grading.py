"""A Verifier provider issue does not overturn T15's own grading of the article (T-20260914-047, case 01)."""
from __future__ import annotations

from aaa.agents.tier1.phases.verification.provider_findings import record_provider_findings

_URI = "minio://eng-01/phase_5/T15.json"
_T15 = {"art72_post_market_plan": {"status": "PASS_WITH_OBSERVATIONS"},
        "art12_record_keeping": {"status": "FAIL"}}
_TIDS = {"T15_monitoring_logging_review": ["Art.12", "Art.72"]}


def _state(description: str) -> dict:
    issue = {"issue_type": "provider_nonconformity", "materiality": "material",
             "severity": "major", "description": description}
    return {"phase_artefacts": {"T15_monitoring_logging_review": {"uri": _URI}},
            "verifier_critiques": {"T15_monitoring_logging_review": {
                "verdict": "accept_with_notes", "issues": [issue]}}}


def _materiality(description: str, load=lambda uri: _T15 if uri == _URI else None) -> str:
    state = _state(description)
    record_provider_findings(state, _TIDS, phase_id="P5", phase_label="Phase 5", load=load)
    [found] = [f for f in state["blocking_findings"] if f["finding_id"].startswith("P5-VER-")]
    return found["materiality"]


def test_an_element_graded_as_an_observation_stays_one() -> None:
    """Case 01: 'data from deployers (Art. 72(2)) is not evidenced' — graded PASS_WITH_OBSERVATIONS."""
    assert _materiality("Data from deployers (Art. 72(2)) is not evidenced.") == "possibly_material"


def test_a_failed_grade_or_an_unreadable_artefact_keeps_the_verifier_s_label() -> None:
    """The cap applies only where the artefact's own grading is known and short of FAIL."""
    assert _materiality("Log retention is missing (Art. 12).") == "material"
    assert _materiality("Data from deployers (Art. 72(2)) is not evidenced.",
                        load=lambda uri: None) == "material"
