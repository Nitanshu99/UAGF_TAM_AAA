"""A finished artefact must not be lost to the envelope it arrived in.

Phase 6 of the 2026-09-09 Mariposa re-run spent 396 s producing a complete T18
and returned it as ``{"tool": "report_render", "args": {"payload": {…}}}``. The
contract assertion reads the top level, so the report was called "not the
artefact it was asked for"; the re-prompt then exhausted the 900 s phase budget
and T17, T18, the PDF and the client brief were all withheld — over a wrapper.
"""
from __future__ import annotations

import pytest

from aaa.tools.evidence_retrieval.terminal_round import close_retrieval, unwrap_tool_envelope

CONTRACT = ("executive_summary", "summary", "rationale_summary")

#: The shape the run actually returned, trimmed to its structure.
WRAPPED = {
    "tool": "report_render",
    "args": {"template_id": "T18_audit_report",
             "payload": {"engagement_id": "eng-06_mariposa_edu_gmbh",
                         "executive_summary": "Mariposa is not in conformity.",
                         "auditor_opinion": {"opinion_type": "adverse"}}},
}


def test_the_report_phase_6_threw_away_is_now_recovered():
    """The acceptance criterion, stated as an assertion."""
    out = unwrap_tool_envelope(WRAPPED, CONTRACT)
    assert out["executive_summary"] == "Mariposa is not in conformity."
    assert out["auditor_opinion"]["opinion_type"] == "adverse"


def test_the_payload_is_returned_not_the_envelope():
    """Downstream must see the artefact, never the wrapper it arrived in."""
    out = unwrap_tool_envelope(WRAPPED, CONTRACT)
    assert "tool" not in out and "args" not in out
    assert out["engagement_id"] == "eng-06_mariposa_edu_gmbh"


def test_args_itself_is_used_when_there_is_no_payload_key():
    """Some replies put the artefact directly under ``args``."""
    wrapped = {"tool": "report_render", "args": {"summary": "done"}}
    assert unwrap_tool_envelope(wrapped, CONTRACT) == {"summary": "done"}


# --------------------------------------------------------------------------
# it can never promote a non-answer
# --------------------------------------------------------------------------
def test_a_wrapper_whose_payload_misses_the_contract_is_left_alone():
    """Unwrapping is gated on the contract; otherwise today's failure stands."""
    wrapped = {"tool": "report_render", "args": {"payload": {"notes": "nothing useful"}}}
    assert unwrap_tool_envelope(wrapped, CONTRACT) is wrapped


def test_a_wrapped_retrieval_plan_is_left_alone():
    """A plan in a wrapper is still a plan (F15), and must fail as one."""
    wrapped = {"tool": "x", "args": {"payload": {"retrieval_plan": {"queries": ["a"]}}}}
    assert unwrap_tool_envelope(wrapped, CONTRACT) is wrapped


def test_a_bare_answer_is_untouched():
    """The common path is unchanged and pays nothing for this."""
    bare = {"executive_summary": "already an answer"}
    assert unwrap_tool_envelope(bare, CONTRACT) is bare


@pytest.mark.parametrize("result", [None, "text", [], {}, {"tool": "x"},
                                    {"tool": "x", "args": "not a dict"}])
def test_shapes_that_carry_no_artefact_are_untouched(result):
    """Anything that is not a tool envelope round-trips identically."""
    assert unwrap_tool_envelope(result, CONTRACT) is result


def test_no_contract_means_no_unwrapping():
    """A caller that asserts nothing gets exactly what the model returned."""
    assert unwrap_tool_envelope(WRAPPED, ()) is WRAPPED


# --------------------------------------------------------------------------
# end to end: the phase no longer spends a re-prompt on it
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_close_retrieval_files_it_without_re_prompting():
    """The 396 s call is accepted, so the budget is never spent on a second."""
    class _Agent:
        name = "ReportArchitect"

        async def acompletion_json(self, *_a, **_k):
            """Fail loudly: reaching here means the artefact was discarded."""
            raise AssertionError("re-prompted despite holding a valid artefact")

    out = await close_retrieval(_Agent(), "phase6_report", {}, WRAPPED, CONTRACT)
    assert out["executive_summary"] == "Mariposa is not in conformity."
