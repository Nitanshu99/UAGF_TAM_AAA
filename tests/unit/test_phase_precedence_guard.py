"""Finding F4 — a phase must not run before the phase it depends on.

Turn 1 of the assessed run dispatched **P2 before P1**, reasoning "Phase 1
artefacts admitted" from three *intake* artefacts whose ids begin ``T01``.
Phase 1's real contract, ``T02_system_card``, did not exist. DataAuditor then
ran on the client's declared risk tier and modality rather than on Phase 1's
confirmed ones, and the run logged zero guard overrides — ``apply_guards`` had
no precedence gate, and ``pending_mandatory`` only ran at close-out.

These tests pin both halves: the guard that corrects the order, and the
observation that stops the model having to infer phase state from an id prefix.
"""
from __future__ import annotations

from aaa.agents.tier1.orchestrator.react import Decision, build_envelope
from aaa.agents.tier1.orchestrator.react.coverage import PHASE_ARTEFACT, phase_progress
from aaa.agents.tier1.orchestrator.react.guards import _PHASE_CAP, apply_guards
from aaa.agents.tier1.orchestrator.react.prereqs import PHASE_PREREQS
from aaa.platform.prompt_registry import load_prompt

#: The plan the CSP solver produced for this engagement.
_PLAN = {"P1": "M", "P2": "M", "P3": "M", "P4": "M", "P5": "M", "P6": "M"}

#: The three intake artefacts the assessed run mistook for Phase 1 output.
_INTAKE = {"T01a_stage_a_triage": {}, "T01b_annex_iv_dossier": {},
           "T01c_intake_completeness_report": {}}


def _state(**over) -> dict:
    state = {"phase_plan": dict(_PLAN), "phase_artefacts": dict(_INTAKE),
             "intake_completeness_score": 1.0}
    state.update(over)
    return state


# --------------------------------------------------------------------------- #
# the guard
# --------------------------------------------------------------------------- #

def test_turn_1_replayed_p2_before_p1_is_redirected():
    """The assessed routing error, through the real guard."""
    out, note = apply_guards(Decision(action="DISPATCH", phase_id="P2",
                                      rationale="Phase 1 artefacts admitted"),
                             _state(), [])

    assert (out.action, out.phase_id) == ("DISPATCH", "P1")
    assert note is not None and "P2 depends on P1" in note


def test_the_intake_artefacts_do_not_satisfy_phase_1():
    """`T01*` is intake; Phase 1's output contract is `T02_system_card`."""
    assert PHASE_ARTEFACT["P1"] == "T02_system_card"
    assert not phase_progress(_state(), [])["completed"]


def test_the_dispatch_is_allowed_once_the_prerequisite_has_delivered():
    """The gate orders the audit; it must not stall it."""
    state = _state(phase_artefacts={**_INTAKE, "T02_system_card": {}})
    decision = Decision(action="DISPATCH", phase_id="P2")
    out, note = apply_guards(decision, state, [])

    assert out is decision and note is None


def test_phase_4_waits_for_phase_3():
    """Phase 3 owns the load-level findings Phase 4 suppresses to avoid duplicating."""
    state = _state(phase_artefacts={**_INTAKE, "T02_system_card": {}})
    out, note = apply_guards(Decision(action="DISPATCH", phase_id="P4"), state, [])

    assert (out.action, out.phase_id) == ("DISPATCH", "P3")
    assert note is not None and "P4 depends on P3" in note


def test_phase_1_itself_has_no_prerequisite():
    """P1 is the entry point; only the intake gate stands in front of it."""
    assert "P1" not in PHASE_PREREQS
    decision = Decision(action="DISPATCH", phase_id="P1")
    out, note = apply_guards(decision, _state(), [])

    assert out is decision and note is None


def test_a_skipped_prerequisite_is_not_a_prerequisite():
    """Under the L-branch P3 is skipped, so P4's dependency does not arise."""
    state = _state(phase_plan={"P1": "M", "P3": "S", "P4": "M", "L": "M"},
                   phase_artefacts={**_INTAKE, "T02_system_card": {},
                                    "T16_uagf_tam_l_evidence": {}})
    decision = Decision(action="DISPATCH", phase_id="P4")
    out, note = apply_guards(decision, state, [])

    assert out is decision and note is None


def test_a_prerequisite_at_its_dispatch_cap_does_not_deadlock_the_audit():
    """A phase tried to the cap has failed; blocking on it forever helps nobody."""
    history = [{"action": "DISPATCH", "phase_id": "P1",
                "outcome": {"new_artefacts": []}}] * _PHASE_CAP
    decision = Decision(action="DISPATCH", phase_id="P2")
    out, note = apply_guards(decision, _state(), history)

    assert (out.action, out.phase_id) == ("DISPATCH", "P2")
    assert note is None


def test_the_guard_never_redirects_onto_a_phase_another_gate_blocks():
    """Rewriting to P1 under a failed intake gate would deadlock on the correction."""
    state = _state(intake_completeness_score=0.5)
    decision = Decision(action="DISPATCH", phase_id="P2")
    out, note = apply_guards(decision, state, [])

    assert (out.action, out.phase_id) == ("DISPATCH", "P2")
    assert note is None


def test_the_art5_halt_still_outranks_precedence():
    """A prohibited practice must not spawn a prerequisite phase."""
    out, note = apply_guards(Decision(action="DISPATCH", phase_id="P2"),
                             _state(risk_tier="prohibited"), [])

    assert out.action == "FINALIZE"
    assert note is not None and "Art.5" in note


def test_the_dispatch_cap_still_outranks_precedence():
    """The more specific existing gates keep precedence, as with the repeat guard."""
    history = [{"action": "DISPATCH", "phase_id": "P2"}] * _PHASE_CAP
    out, _ = apply_guards(Decision(action="DISPATCH", phase_id="P2"), _state(), history)

    assert out.action == "ASSEMBLE_MATRIX"


def test_dispatch_p6_is_the_close_out_and_is_gated_like_one():
    """The loop runs the report and stops on `DISPATCH P6` — so the gates must see it.

    Found while building the precedence map: `DISPATCH P6` reached Phase 6
    through neither the mandatory-phase check nor matrix-before-finalize, both
    of which tested the action name rather than what the loop does with it.
    """
    out, note = apply_guards(Decision(action="DISPATCH", phase_id="P6"), _state(), [])

    assert (out.action, out.phase_id) == ("DISPATCH", "P1")
    assert note is not None and "overstate conformity" in note

    ran = _state(phase_plan={"P1": "M"},
                 phase_artefacts={**_INTAKE, "T02_system_card": {}})
    out, note = apply_guards(Decision(action="DISPATCH", phase_id="P6"), ran, [])
    assert out.action == "ASSEMBLE_MATRIX"
    assert note is not None and "compliance matrix" in note


# --------------------------------------------------------------------------- #
# the observation
# --------------------------------------------------------------------------- #

def test_the_envelope_states_phase_state_instead_of_implying_it():
    """What the model had to infer from `T01*` it is now simply told."""
    summary = build_envelope(_state(), [])["audit_state_summary"]

    assert summary["phases_completed"] == []
    assert summary["phases_outstanding"] == ["P1", "P2", "P3", "P4", "P5"]
    assert "T01a_stage_a_triage" in [
        a["template_id"] for a in summary["phase_artefacts_admitted"]], (
        "the artefact list still says what exists")


def test_the_envelope_tracks_completion_as_phases_deliver():
    """A phase counts as complete on its output contract, not on being dispatched."""
    state = _state(phase_artefacts={**_INTAKE, "T02_system_card": {},
                                    "T06_datasheet_for_datasets": {}})
    summary = build_envelope(state, [])["audit_state_summary"]

    assert summary["phases_completed"] == ["P1", "P2"]
    assert summary["phases_outstanding"] == ["P3", "P4", "P5"]


def test_a_tier3_spawn_counts_as_run_when_it_was_dispatched():
    """CYBER/PRIVACY have no artefact contract, so dispatch is the only evidence."""
    state = _state(phase_plan={"P1": "M", "CYBER": "M", "PRIV": "M"},
                   phase_artefacts={**_INTAKE, "T02_system_card": {}})
    history = [{"action": "DISPATCH", "phase_id": "CYBER"}]
    summary = build_envelope(state, history)["audit_state_summary"]

    assert summary["phases_completed"] == ["P1", "CYBER"]
    assert summary["phases_outstanding"] == ["PRIV"]


# --------------------------------------------------------------------------- #
# through the real ReAct loop
# --------------------------------------------------------------------------- #

async def test_the_assessed_sequence_replayed_through_the_loop(monkeypatch):
    """Turn 1's P2-before-P1, replayed over the real loop and stub runners.

    The model keeps proposing what it proposed in the assessed run; the audit
    now runs the prerequisite first and every override is on the record.
    """
    from aaa.agents.tier1.orchestrator.react import act as act_mod
    from aaa.agents.tier1.orchestrator.react import loop as loop_mod
    from tests.unit.support.react_helpers import FakeOrchestrator, stub_runners

    order: list[str] = []
    monkeypatch.setattr(loop_mod, "node_stage0", lambda s: s)
    monkeypatch.setattr(act_mod, "node_plan", lambda s: {**s, "phase_plan": dict(_PLAN)})
    monkeypatch.setattr(act_mod, "node_compliance_matrix",
                        lambda s: {**s, "compliance_matrix": {"Art.10": "PASS"}})
    monkeypatch.setattr(act_mod, "node_hitl_checkpoint", lambda s: s)
    monkeypatch.setattr(act_mod, "RUNNERS", stub_runners(order))
    orch = FakeOrchestrator([
        {"action": "PLAN", "rationale": "plan first"},
        {"action": "DISPATCH", "phase_id": "P2",     # the assessed turn 1
         "rationale": "Phase 1 artefacts admitted; intake completeness 1.0"},
        {"action": "DISPATCH", "phase_id": "P2"},
        {"action": "DISPATCH", "phase_id": "P4"},    # ahead of P3
        {"action": "DISPATCH", "phase_id": "P4"},
        {"action": "DISPATCH", "phase_id": "P5"},
        {"action": "ASSEMBLE_MATRIX"},
        {"action": "FINALIZE", "rationale": "report time"},
    ])

    state = await loop_mod.run_react(
        orch, {}, {"engagement_id": "eng-01_finclear_gmbh",
                   "intake_completeness_score": 1.0,
                   "phase_artefacts": dict(_INTAKE)})

    assert order == ["P1", "P2", "P3", "P4", "P5", "P6"], (
        "the assessed run executed P2 first and never ran P1")
    overrides = [h["guard_override"] for h in state["react_decision_history"]
                 if h.get("guard_override")]
    assert any("P2 depends on P1" in o for o in overrides)
    assert any("P4 depends on P3" in o for o in overrides)
    corrected = next(h for h in state["react_decision_history"]
                     if h.get("proposed_phase_id") == "P2")
    assert corrected["phase_id"] == "P1", "the override must be legible as one"


# --------------------------------------------------------------------------- #
# prompt / contract agreement
# --------------------------------------------------------------------------- #

def test_the_prompt_states_the_rule_the_runtime_enforces():
    """A gate the model is not told about is a gate it can only trip over."""
    prompt = load_prompt("orchestrator")

    assert "Phase precedence" in prompt
    assert "T02_system_card" in prompt
    assert "phases_outstanding" in prompt


def test_every_prerequisite_is_a_phase_the_model_may_dispatch():
    """A rewrite onto a phase id the parser rejects would kill the turn."""
    from aaa.agents.tier1.orchestrator.react import DISPATCHABLE_PHASES

    for phase, prereqs in PHASE_PREREQS.items():
        assert phase in DISPATCHABLE_PHASES, phase
        for prereq in prereqs:
            assert prereq in DISPATCHABLE_PHASES, prereq
            assert prereq in PHASE_ARTEFACT, (
                f"{prereq} has no output contract, so 'has it run' is undecidable")


def test_the_prereq_map_agrees_with_the_wrap_up_order():
    """The rescue and the guard must not disagree about what comes first."""
    from aaa.agents.tier1.orchestrator.react.coverage import PIPELINE_ORDER

    for phase, prereqs in PHASE_PREREQS.items():
        key = "PRIV" if phase == "PRIVACY" else phase
        for prereq in prereqs:
            assert PIPELINE_ORDER.index(prereq) < PIPELINE_ORDER.index(key), (
                f"{prereq} must precede {phase} in the wrap-up order too")
