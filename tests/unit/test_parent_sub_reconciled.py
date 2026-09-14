"""Fix 43 — a paragraph and its requirement, reconciled in T17 (finding R11).

The delivered matrices carry pairs a regulator cannot read without explanation:

    case 03    Art.15   FAIL                    Art.15§1   PASS_WITH_OBSERVATIONS
    case 05    Art.15   PASS_WITH_OBSERVATIONS  Art.15§1   INSUFFICIENT_EVIDENCE

**Fix 47 was applied first, as the backlog required, and R11 survived it** — it
removed the mis-attributed half and left a correctly-attributed divergence, moving
the pair to `Art.10` / `Art.10§2(f)` in both cases. So this is a presentation
repair, and only that: the verdicts are untouched.
"""
from __future__ import annotations

import pytest

from aaa.agents.tier1.phases.compliance_matrix.derive_verdicts import _derive_verdicts
from aaa.agents.tier1.phases.compliance_matrix.evidence_entry import _evidence_entry
from aaa.agents.tier1.phases.compliance_matrix.parent_sub import relation_note

#: The run's own two pairs, in both directions.
CASE_03 = {"Art.15": "FAIL", "Art.15§1": "PASS_WITH_OBSERVATIONS"}
CASE_05 = {"Art.15": "PASS_WITH_OBSERVATIONS", "Art.15§1": "INSUFFICIENT_EVIDENCE"}


def _note(matrix: dict[str, str], article: str) -> str:
    return relation_note(article, matrix[article], matrix)


# --------------------------------------------------------------------------- #
# a divergent pair is reconciled, in both directions
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("matrix,name", [(CASE_03, "case 03"), (CASE_05, "case 05")])
def test_the_paragraph_names_its_requirements_verdict(matrix, name):
    note = _note(matrix, "Art.15§1")
    assert "Art.15 §1 is a paragraph of Art.15" in note
    assert matrix["Art.15"] in note
    assert "may legitimately differ" in note


@pytest.mark.parametrize("matrix,name", [(CASE_03, "case 03"), (CASE_05, "case 05")])
def test_the_requirement_names_its_paragraphs_verdict(matrix, name):
    note = _note(matrix, "Art.15")
    assert "paragraphs are reported separately" in note
    assert f"Art.15 §1 ({matrix['Art.15§1']})" in note
    assert "not the sum of its paragraphs'" in note


def test_the_clause_distinguishes_a_conclusion_from_its_absence():
    """FAIL and INSUFFICIENT_EVIDENCE are different kinds of answer, not severities."""
    unassessed = _note(CASE_05, "Art.15§1")
    assert "could not be assessed on the evidence available" in unassessed

    both_concluded = _note(CASE_03, "Art.15§1")
    assert "each rests on its own admitted artefacts" in both_concluded
    assert "could not be assessed" not in both_concluded


def test_the_two_directions_read_from_their_own_row():
    sub = _note(CASE_05, "Art.15§1")
    parent = _note(CASE_05, "Art.15")
    assert "this row could not be assessed" in sub
    assert "the other could not be assessed" in parent


# --------------------------------------------------------------------------- #
# a non-divergent pair gains nothing
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("verdict", ["PASS", "FAIL", "INSUFFICIENT_EVIDENCE"])
def test_an_agreeing_pair_says_nothing(verdict):
    matrix = {"Art.15": verdict, "Art.15§1": verdict}
    assert _note(matrix, "Art.15") == ""
    assert _note(matrix, "Art.15§1") == ""


def test_a_paragraph_whose_parent_is_not_in_the_matrix_says_nothing():
    assert relation_note("Art.15§1", "PASS", {"Art.15§1": "PASS"}) == ""


def test_a_plain_article_with_no_paragraphs_says_nothing():
    assert relation_note("Art.9", "FAIL", {"Art.9": "FAIL", "Art.10": "PASS"}) == ""


def test_an_entry_built_without_the_matrix_reconciles_nothing():
    """A caller building one entry in isolation gets no invented relationship."""
    entry = _evidence_entry({}, "Art.15§1", "PASS", [])
    assert "paragraph of" not in entry["rationale"]


# --------------------------------------------------------------------------- #
# the verdicts themselves are untouched
# --------------------------------------------------------------------------- #

def _state(**kw) -> dict:
    return {"engagement_id": "eng-t", "risk_tier": "high", "declared_risk_tier": "high",
            "phase_artefacts": {}, "verifier_critiques": {}, **kw}


def test_a_reconciled_pair_keeps_both_verdicts():
    state = _state(
        insufficient_evidence_articles=["Art.15§1"],
        blocking_findings=[{"finding_id": "X", "materiality": "material",
                            "eu_ai_act_articles": ["Art.15"], "description": "probe failed"}])
    _derive_verdicts(state)
    assert state["compliance_matrix"]["Art.15"] == "FAIL"
    assert state["compliance_matrix"]["Art.15§1"] == "INSUFFICIENT_EVIDENCE"
    assert "paragraph of Art.15" in state["article_evidence"]["Art.15§1"]["rationale"]
    assert "paragraphs are reported separately" in state["article_evidence"]["Art.15"]["rationale"]


def test_every_verdict_is_decided_before_any_rationale_is_written():
    """Ordering: a row's rationale names a sibling's verdict, so all must exist first."""
    import inspect
    src = inspect.getsource(_derive_verdicts)
    matrix_at = src.index("matrix: dict[str, str] = {")
    evidence_at = src.index("evidence: dict[str, dict] = {")
    assert matrix_at < evidence_at
    assert "_evidence_entry" not in src[matrix_at:evidence_at]
