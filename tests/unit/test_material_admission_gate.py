"""An artefact carrying a confirmed material non-conformity is not evidence (M2).

``PROMPT.md`` reserves ``ESCALATE_HITL`` for ``factual_accuracy = 0`` *or* "a
confirmed material non-conformity". At call #040 of the 2026-09-10 Mariposa run
the Verifier returned ``ACCEPT_WITH_OBSERVATIONS`` on T10 at 8/15 while recording
two issues at ``severity: critical, materiality: material``. Nothing read them:
admission was decided by the verdict string alone.
"""
from __future__ import annotations

import logging

import pytest

from aaa.agents.tier1.verifier.issues import _normalise_issues, material_non_conformity
from aaa.agents.tier1.verifier.verdict_codes import _map_llm_verdict
from aaa.agents.tier1.verifier.verdicts import MAX_RERUNS

_MATERIAL = {"severity": "critical", "field": "global_explanation.technique",
             "description": "Declared technique contradicts the one used.",
             "materiality": "material"}
_POSSIBLY = {**_MATERIAL, "materiality": "possibly_material"}
_NOT = {**_MATERIAL, "materiality": "not_material"}


def test_material_non_conformity_finds_the_blocker():
    assert material_non_conformity(_normalise_issues([_NOT, _MATERIAL]))["field"] == \
        "global_explanation.technique"


@pytest.mark.parametrize("issue", [_POSSIBLY, _NOT])
def test_a_sub_material_issue_does_not_block(issue):
    """Only a *confirmed* material finding is incompatible with admission."""
    assert material_non_conformity(_normalise_issues([issue])) is None


@pytest.mark.parametrize("raw", ["ACCEPT", "ACCEPT_WITH_OBSERVATIONS"])
@pytest.mark.parametrize("reruns", [0, 1, MAX_RERUNS])
def test_a_material_issue_goes_straight_to_human_review(raw, reruns):
    """M20: the rule reserves ESCALATE_HITL for exactly this, and the
    verification run repaired 0 of 13 such artefacts by re-running them."""
    assert _map_llm_verdict(raw, _normalise_issues([_MATERIAL]), [],
                            reruns) == "escalate_hitl"


def test_the_refusal_is_logged_with_the_field_it_names(caplog):
    with caplog.at_level(logging.WARNING):
        _map_llm_verdict("ACCEPT", _normalise_issues([_MATERIAL]), [], 0)
    assert "confirmed material" in caplog.text
    assert "global_explanation.technique" in caplog.text


@pytest.mark.parametrize("raw,expected", [
    ("ACCEPT", "accept"), ("ACCEPT_WITH_OBSERVATIONS", "accept_with_notes")])
def test_a_clean_artefact_is_still_admitted(raw, expected):
    """The gate must not touch the ordinary case."""
    assert _map_llm_verdict(raw, _normalise_issues([_POSSIBLY]), [], 0) == expected


def test_an_already_failing_verdict_is_untouched():
    assert _map_llm_verdict("ESCALATE_HITL", _normalise_issues([_MATERIAL]), [], 0) == \
        "escalate_hitl"


def test_call_040_would_no_longer_be_admitted():
    """The assessed reply, in the shape it arrived."""
    issues = _normalise_issues([
        {"severity": "critical", "field": "global_explanation.technique",
         "description": "…", "materiality": "material"},
        {"severity": "critical", "field": "local_explanations[].prediction",
         "description": "…", "materiality": "material"},
        {"severity": "minor", "field": "sample_size",
         "description": "…", "materiality": "not_material"}])
    assert _map_llm_verdict("ACCEPT_WITH_OBSERVATIONS", issues, [], 0) == "escalate_hitl"


# --- M20: the report-template downgrade must not re-admit a blocked artefact --

def _critique(issues, factual_accuracy=2):
    return {"verdict": "escalate_hitl", "issues": _normalise_issues(issues),
            "notes": [], "scores": {"factual_accuracy": factual_accuracy}}


def _run_downgrade(tid, critique):
    """Run the real report-template downgrade on one critique.

    The rule used to be inline in ``_critique_artefact`` and was replayed here;
    it now lives in its own module, so this exercises the shipping code rather
    than a copy of it.
    """
    from aaa.agents.tier1.phases.verification.downgrade import downgrade_report_escalation
    state = {"verifier_critiques": {tid: dict(critique)}}
    return downgrade_report_escalation(state, tid, critique["verdict"], "P3 test")


def test_a_report_template_escalation_still_downgrades_when_not_material():
    """The existing rule is unchanged for the case it was written for."""
    assert _run_downgrade("T18_audit_report", _critique([_NOT])) == "accept_with_notes"


def test_a_material_finding_survives_the_report_template_downgrade():
    """Otherwise T17/T18 would re-admit exactly what the gate refused."""
    assert _run_downgrade("T18_audit_report", _critique([_MATERIAL])) == "escalate_hitl"
    assert _run_downgrade("T17_compliance_matrix", _critique([_MATERIAL])) == "escalate_hitl"


def test_a_non_report_artefact_is_untouched_by_the_downgrade():
    assert _run_downgrade("T09_model_card", _critique([_NOT])) == "escalate_hitl"
