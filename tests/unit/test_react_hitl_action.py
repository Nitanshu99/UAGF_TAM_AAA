"""Finding F8 — the Orchestrator must be able to say what it is ordered to say.

`ACTIONS` had no HITL token while the prompt commanded "pause the audit and emit
a HITL alert", so the model emitted the least-wrong legal move — `PLAN` — 22
times in a row, narrating "Audit remains paused" while nothing changed. 570 s and
~119,000 tokens produced zero state changes, and exhausting the turn budget
silently cancelled six mandatory phases.

Two things were wrong and both are pinned here: the missing token, and the
instruction itself — the runtime has not paused on HITL since the
provisional-report rework, so "pause" was uninstructable *and* untrue.
"""
from __future__ import annotations

from aaa.agents.tier1.orchestrator.react import ACTIONS, Decision, parse_decision
from aaa.agents.tier1.orchestrator.react.escalate import record_escalation
from aaa.agents.tier1.orchestrator.react.guards import _PHASE_CAP, apply_guards
from aaa.platform.prompt_registry import load_prompt

# --------------------------------------------------------------------------- #
# the vocabulary
# --------------------------------------------------------------------------- #

def test_escalate_hitl_is_in_the_action_vocabulary():
    """The token the prompt has always demanded now exists."""
    assert "ESCALATE_HITL" in ACTIONS
    assert parse_decision({"action": "ESCALATE_HITL",
                           "rationale": "T06 num_instances contradiction"}).action \
        == "ESCALATE_HITL"


def test_escalate_hitl_needs_no_phase_id():
    """Unlike DISPATCH, an escalation is about the engagement, not a phase."""
    assert parse_decision({"action": "escalate_hitl"}).phase_id is None


def test_hitl_phrasings_normalise_onto_the_token():
    """The prompt's own wording ('pause') must not be rejected as unknown."""
    for raw in ("HITL", "escalate", "Escalate to HITL", "hitl_alert", "PAUSE_AUDIT"):
        assert parse_decision({"action": raw}).action == "ESCALATE_HITL", raw


def test_unknown_actions_are_still_rejected():
    """Tolerance must not become a wildcard."""
    import pytest

    from aaa.agents.tier1.orchestrator.react import DecisionError
    with pytest.raises(DecisionError):
        parse_decision({"action": "DO_EVERYTHING"})


# --------------------------------------------------------------------------- #
# what the action does
# --------------------------------------------------------------------------- #

def test_escalation_records_the_rationale_as_the_reviewer_alert():
    """The rationale is the alert text, not decoration on a flag."""
    state: dict = {}
    record_escalation(state, "T08 asserts Art. 10§5 N/A but the declaration invokes it.")

    assert state["hitl_required"] is True
    assert "Art. 10§5" in state["hitl_reason"]


def test_escalation_appends_to_a_reason_a_phase_already_recorded():
    """An engagement can be escalated for more than one thing."""
    state = {"hitl_required": True,
             "hitl_reason": "Phase 2 DataAuditor: Verifier verdict 'escalate_hitl'."}
    record_escalation(state, "Declaration mismatch on sensitive_feature_columns.")

    assert "Phase 2 DataAuditor" in state["hitl_reason"]
    assert "Declaration mismatch" in state["hitl_reason"]


def test_escalation_does_not_duplicate_the_same_alert():
    """Re-recording the same concern must not grow the reason unboundedly."""
    state: dict = {}
    record_escalation(state, "same concern")
    record_escalation(state, "same concern")
    assert state["hitl_reason"].count("same concern") == 1


def test_escalation_reaches_the_human_review_packet():
    """The alert must arrive where a reviewer actually reads it."""
    from aaa.tools.hitl_review import build_hitl_review_packet

    state: dict = {"engagement_id": "eng-t", "verifier_critiques": {}}
    record_escalation(state, "T06 num_instances = 0 contradicts 1000 declared.")
    packet = build_hitl_review_packet(state)

    assert packet["hitl_required"] is True
    assert "num_instances" in packet["hitl_reason"]
    assert packet["orchestrator_alerts"] == [
        "T06 num_instances = 0 contradicts 1000 declared."]


def test_alert_survives_a_later_phase_overwriting_hitl_reason():
    """`hitl_reason` has ~a dozen writers; the alert must not depend on it."""
    from aaa.agents.tier1.phases.verification.finish_phase import _finish_phase
    from aaa.tools.hitl_review import build_hitl_review_packet

    state: dict = {"engagement_id": "eng-t", "verifier_critiques": {}}
    record_escalation(state, "Art. 10§5 derogation claim unreconciled.")
    _finish_phase(state, "escalate_hitl", 0, "Phase 3 ModelValidator", 0.0)

    assert "Art. 10§5" not in (state["hitl_reason"] or ""), (
        "precondition: the phase does overwrite hitl_reason")
    assert build_hitl_review_packet(state)["orchestrator_alerts"] == [
        "Art. 10§5 derogation claim unreconciled."]


# --------------------------------------------------------------------------- #
# the livelock guard
# --------------------------------------------------------------------------- #

def _history(action: str, phase_id=None, new_artefacts=()):
    return [{"action": action, "phase_id": phase_id,
             "outcome": {"new_artefacts": list(new_artefacts)}}]


def test_repeated_no_op_plan_is_redirected_to_outstanding_work():
    """The assessed livelock: PLAN after a PLAN that admitted nothing."""
    state = {"phase_plan": {"P1": "M", "P2": "M"}, "phase_artefacts": {}}
    out, note = apply_guards(Decision(action="PLAN"), state, _history("PLAN"))

    assert out.action == "DISPATCH" and out.phase_id == "P1"
    assert note is not None and "repeats the previous turn" in note


def test_repeated_escalation_is_redirected_too():
    """Adding the token must not simply relocate the livelock."""
    state = {"phase_plan": {"P1": "M"}, "phase_artefacts": {},
             "hitl_required": True, "hitl_reason": "already flagged"}
    out, note = apply_guards(Decision(action="ESCALATE_HITL"), state,
                             _history("ESCALATE_HITL"))

    assert out.action == "DISPATCH" and out.phase_id == "P1"
    assert note is not None


def test_first_escalation_passes_through():
    """One escalation is legitimate; only the repeat is not."""
    state = {"phase_plan": {"P1": "M"}, "phase_artefacts": {}}
    decision = Decision(action="ESCALATE_HITL", rationale="T06 contradiction")
    out, note = apply_guards(decision, state, _history("DISPATCH", "P2"))

    assert out is decision and note is None


def test_a_productive_repeat_is_not_redirected():
    """A repeat that admitted an artefact is real work, not a livelock."""
    state = {"phase_plan": {"P1": "M"}, "phase_artefacts": {}}
    decision = Decision(action="DISPATCH", phase_id="P1")
    out, note = apply_guards(decision, state,
                             _history("DISPATCH", "P1", ["T02_system_card"]))

    assert out is decision and note is None


def test_dispatching_a_different_phase_is_not_a_repeat():
    """Same action, different phase, is ordinary sequencing.

    P1 carries its artefact here because the precedence gate (F4, fix 8) now
    runs first: without it the dispatch is redirected to the prerequisite and
    this test would pass for the wrong reason.
    """
    state = {"phase_plan": {"P1": "M"}, "phase_artefacts": {"T02_system_card": {}}}
    decision = Decision(action="DISPATCH", phase_id="P3")
    out, note = apply_guards(decision, state, _history("DISPATCH", "P2"))

    assert out is decision and note is None


def test_repeat_with_no_work_left_closes_the_audit():
    """With every mandatory artefact in and a matrix built, forward is FINALIZE."""
    state = {"phase_plan": {"P1": "M"}, "phase_artefacts": {"T02_system_card": {}},
             "compliance_matrix": {"Art.6": "PASS"}}
    out, note = apply_guards(Decision(action="ESCALATE_HITL"), state,
                             _history("ESCALATE_HITL"))

    assert out.action == "FINALIZE"
    assert note is not None


def test_guard_never_rewrites_a_decision_to_itself():
    """A self-rewrite would be a livelock the guard manufactured."""
    state = {"phase_plan": {"P1": "M"}, "phase_artefacts": {}}
    out, note = apply_guards(Decision(action="DISPATCH", phase_id="P1"), state,
                             _history("DISPATCH", "P1"))

    # P1 is owed and was just dispatched fruitlessly: the ladder would point back
    # at P1, so the decision is left alone rather than redirected to itself.
    assert (out.action, out.phase_id) == ("DISPATCH", "P1")
    assert note is None


def test_dispatch_cap_still_wins_over_the_repeat_guard():
    """The more specific existing gates keep precedence."""
    history = [{"action": "DISPATCH", "phase_id": "P3",
                "outcome": {"new_artefacts": []}}] * _PHASE_CAP
    out, _ = apply_guards(Decision(action="DISPATCH", phase_id="P3"), {}, history)
    assert out.action == "ASSEMBLE_MATRIX"


# --------------------------------------------------------------------------- #
# the prompt half of F8
# --------------------------------------------------------------------------- #

def test_prompt_no_longer_orders_a_pause_the_runtime_does_not_perform():
    """The runtime has not halted on HITL since the provisional-report rework."""
    prompt = load_prompt("orchestrator")
    assert "pause the audit" not in prompt
    assert "escalate to HITL before proceeding" not in prompt


def test_every_action_the_prompt_offers_is_one_the_parser_accepts():
    """The F8 failure mode: an instruction the contract cannot represent."""
    prompt = load_prompt("orchestrator")
    for action in ACTIONS:
        assert action in prompt, f"{action} is not offered to the model"
    assert "ESCALATE_HITL` records a human-review alert" in prompt
