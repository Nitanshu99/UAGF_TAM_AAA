"""eval_inputs() must prefer a real resolved golden set over the demo defaults.

Regression test for the dead-field bug: decl.get("eval_questions", <2-question
demo default>) was the only path ever exercised, so every agentic/LLM
engagement was evaluated against the same two hardcoded Q&A pairs regardless
of what golden_set_uri the client actually submitted.
"""
from __future__ import annotations

import json
import pathlib

from aaa.agents.tier3.uagf_tam_l.evals import eval_inputs
from aaa.agents.tier3.uagf_tam_l.golden_set import resolve_golden_set
from aaa.agents.tier3.uagf_tam_l.ragas_run import run_golden_set

_DEMO_QUESTIONS = ["What is the EU AI Act?", "Define Article 10."]
_LEGALMIND_STAGE_B = (
    pathlib.Path(__file__).resolve().parents[2] / "mock/04_legalmindd_ai_ltd/stage_b.json")
_REAL_GOLDEN_SET = (
    ["Real client question 1", "Real client question 2", "Real client question 3"],
    [["ctx1"], ["ctx2"], ["ctx3"]],
    ["Real answer 1", "Real answer 2", "Real answer 3"],
    ["Real expected 1", "Real expected 2", "Real expected 3"],
)


def test_real_golden_set_overrides_the_demo_default():
    """A resolved golden set changes eval_inputs()'s output, not the demo pairs."""
    questions, contexts, answers, expected = eval_inputs({}, golden_set=_REAL_GOLDEN_SET)
    assert questions == _REAL_GOLDEN_SET[0]
    assert contexts == _REAL_GOLDEN_SET[1]
    assert answers == _REAL_GOLDEN_SET[2]
    assert expected == _REAL_GOLDEN_SET[3]
    assert questions != _DEMO_QUESTIONS


def test_no_golden_set_yields_nothing_to_evaluate():
    """No client golden set means no evaluation, not an invented one.

    This asserted the demo pairs until 2026-09-11. Standing in two questions
    about the EU AI Act and publishing the resulting pass rate in the client's
    report states a measurement of their system that was never taken.
    """
    assert eval_inputs({}, golden_set=None) == ([], [], [], [])


def test_a_zero_row_golden_set_yields_nothing_to_evaluate():
    """A file with no usable rows is the same position — and never crashes."""
    assert eval_inputs({}, golden_set=([], [], [], [])) == ([], [], [], [])


def test_an_absent_golden_set_is_reported_unscored_not_failed():
    """`run_golden_set` must say why, rather than return a 0 % pass rate."""
    result = run_golden_set([], [], [])
    assert result["pass_rate"] is None
    assert result["scored"] is False
    assert "No golden evaluation set was supplied" in result["unscored_reason"]


def test_a_caller_supplied_evaluation_set_is_still_honoured():
    """Explicit evaluation data in the dispatch is real input, not a default."""
    decl = {"eval_questions": ["Q"], "eval_answers": ["A"], "eval_expected": ["A"]}
    questions, _c, answers, expected = eval_inputs(decl, golden_set=None)
    assert (questions, answers, expected) == (["Q"], ["A"], ["A"])


def test_golden_set_takes_precedence_over_decl_eval_questions_too():
    """A real golden set wins even over legacy decl["eval_questions"] overrides."""
    decl = {"eval_questions": ["legacy override question"]}
    questions, *_ = eval_inputs(decl, golden_set=_REAL_GOLDEN_SET)
    assert questions == _REAL_GOLDEN_SET[0]


def test_the_shipped_legalmind_golden_set_actually_resolves():
    """The mock/04 fixture must satisfy resolve_golden_set's row contract.

    The tests above use synthetic rows, so they stayed green while the real
    fixture shipped ``reference`` (a citation) and no ``expected`` — every row
    was dropped by ``_row_tuple``, ``resolve_golden_set`` returned ``None`` on
    a log line, and LexAI's whole L-branch verdict was computed on the two
    demo pairs. Loading the file itself is the only assertion that catches it.
    """
    stage_b = json.loads(_LEGALMIND_STAGE_B.read_text())
    resolved = resolve_golden_set(stage_b, store=None)

    assert resolved is not None, "the shipped golden set produced no usable rows"
    questions, contexts, answers, expected = resolved
    assert len(questions) == 60
    assert len({len(questions), len(contexts), len(answers), len(expected)}) == 1

    # The regression that would otherwise return silently.
    assert eval_inputs({}, golden_set=resolved)[0][0] not in _DEMO_QUESTIONS
    # A context is what ragas scores faithfulness against; a corpus tag is not one.
    assert all(len(" ".join(ctx)) > 100 for ctx in contexts)


def test_the_shipped_legalmind_golden_set_is_not_self_scoring():
    """Its answers must be graded against references, not against themselves.

    ``expected`` equal to ``answer`` would make ``run_golden_set``'s
    containment test tautological and hand the branch a 1.0 pass rate that
    measures nothing.
    """
    resolved = resolve_golden_set(json.loads(_LEGALMIND_STAGE_B.read_text()), store=None)
    assert resolved is not None
    questions, _contexts, answers, expected = resolved

    graded = run_golden_set(questions, answers, expected)
    assert 0 < graded["failed_samples"] < graded["total_samples"]
    assert graded["pass_rate"] == 0.85
