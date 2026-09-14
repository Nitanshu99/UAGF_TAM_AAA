"""A procedure that did not run is a scope limitation; it removes evidence only when nothing sufficient ran.

Tier-3 spawns decided nothing on their own: two never reached the confidence gate,
and the third reported a number no rule tied to what had run. The audit programme
reads recorded outcomes instead (ISAE 3000 / ISA 705 scope limitations).
"""
from __future__ import annotations

import pytest

from aaa.agents.tier1.phases.agent_runner.apply_delta import _apply_delta
from aaa.agents.tier2.report_architect.opinion import auditor_opinion
from aaa.platform.audit_programme import PROGRAMME, apply_audit_programme, outcome
from aaa.platform.state.run_integrity import build_run_integrity


def _state(*outcomes: dict) -> dict:
    state: dict = {"phase_artefacts": {}}
    for delta in outcomes:
        _apply_delta(state, {"procedure_outcomes": delta})
    return state


def test_a_supplementary_procedure_not_performed_is_disclosed_and_changes_nothing() -> None:
    state = _state(outcome("robustness_probe", True), outcome("metric_suite", True),
                   outcome("specialist_adversarial_probe", False, "no model endpoint"))
    limits = apply_audit_programme(state)
    assert [(x["procedure"], x["effect"]) for x in limits] == [
        ("specialist_adversarial_probe", "disclosed")]
    assert state["insufficient_evidence_articles"] == []


def test_a_required_element_with_no_sufficient_procedure_performed_is_unevidenced() -> None:
    state = _state(outcome("golden_set_evaluation", False, "no system answers"),
                   outcome("prompt_injection_suite", False, "no endpoint"),
                   outcome("specialist_adversarial_probe", False, "no endpoint"))
    limits = apply_audit_programme(state)
    effects = {x["procedure"]: x["effect"] for x in limits}
    assert effects == {"golden_set_evaluation": "article_unevidenced",
                       "prompt_injection_suite": "article_unevidenced",
                       "specialist_adversarial_probe": "disclosed"}
    assert state["insufficient_evidence_articles"] == ["Art.15"]


def test_another_sufficient_procedure_covers_the_element() -> None:
    """The golden set did not run, but Phase 3 recomputed accuracy: Art. 15 keeps its evidence."""
    state = _state(outcome("golden_set_evaluation", False, "no system answers"),
                   outcome("metric_suite", True))
    limits = apply_audit_programme(state)
    assert [x["effect"] for x in limits] == ["disclosed"]
    assert "Art.15" not in state["insufficient_evidence_articles"]


def test_a_rerun_replaces_the_earlier_outcome_and_the_rule_is_idempotent() -> None:
    state = _state(outcome("metric_suite", False, "first attempt"), outcome("metric_suite", True))
    assert apply_audit_programme(state) == apply_audit_programme(state) == []
    assert state["procedure_outcomes"]["metric_suite"]["outcome"] == "performed"


def test_limitations_reach_the_opinion_and_run_integrity() -> None:
    state = _state(outcome("pii_deep_dive", False, "no dataset to scan"))
    apply_audit_programme(state)
    scope = auditor_opinion({"scope_limitations": state["scope_limitations"]}, "FAIL")["scope_paragraph"]
    assert "Supplementary procedures not performed" in scope and "no dataset to scan" in scope
    assert build_run_integrity(state)["scope_limitations"][0]["procedure"] == "pii_deep_dive"


def test_every_procedure_names_a_real_article_and_unknown_ids_are_refused() -> None:
    assert {p.article for p in PROGRAMME.values()} <= {"Art.10", "Art.15"}
    with pytest.raises(KeyError):
        outcome("no_such_procedure", True)
