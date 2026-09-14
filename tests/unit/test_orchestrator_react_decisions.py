"""ReAct decision contract: action parsing and payload validation."""
from __future__ import annotations

import pytest

from aaa.agents.tier1.orchestrator.react import DecisionError, parse_decision


def test_parse_accepts_every_protocol_action():
    """Each protocol action parses; case/whitespace tolerated."""
    for action in ("PLAN", "dispatch", " Escalate_Hitl ", " Assemble_Matrix ",
                   "FINALIZE"):
        payload = {"action": action}
        if action.strip().upper() == "DISPATCH":
            payload["phase_id"] = "P2"
        assert parse_decision(payload).action == action.strip().upper()


def test_parse_accepts_prompt_md_dispatch_envelope():
    """PROMPT.md documents {"message_type": "Dispatch", …} with no action field."""
    decision = parse_decision({
        "message_type": "Dispatch", "phase_id": "P1",
        "task_brief": "Execute Phase 1 scope triage.",
    })
    assert decision.action == "DISPATCH"
    assert decision.phase_id == "P1"
    assert decision.task_brief.startswith("Execute Phase 1")


def test_parse_rejects_non_dict_and_unknown_action():
    """Non-object payloads and unknown actions raise DecisionError."""
    with pytest.raises(DecisionError):
        parse_decision(["DISPATCH"])
    with pytest.raises(DecisionError):
        parse_decision({"action": "DO_EVERYTHING"})


def test_parse_dispatch_requires_known_phase():
    """DISPATCH without a recognised phase_id is rejected."""
    with pytest.raises(DecisionError):
        parse_decision({"action": "DISPATCH", "phase_id": "P99"})
    ok = parse_decision({"action": "DISPATCH", "phase_id": "cyber"})
    assert ok.phase_id == "CYBER"


def test_parse_unwraps_decision_sequence_wrapper():
    """A wrapped single decision still parses (observed NIM output shape)."""
    decision = parse_decision({"decision_sequence": [
        {"step": "run_csp_solver", "csp_solver_call": {"audit_state": {}}}]})
    assert decision.action == "PLAN"


def test_parse_maps_csp_solver_step_to_plan():
    """PROMPT.md names csp_solver as the PLAN tool."""
    assert parse_decision({"step": "csp_solver"}).action == "PLAN"


def test_parse_unwraps_bare_list():
    """A top-level list of one decision is unwrapped rather than rejected."""
    assert parse_decision([{"action": "FINALIZE"}]).action == "FINALIZE"
