"""Fix 26 (Q1) — an escalated artefact's articles reach the matrix, not the void.

The post-fix part-2 run delivered a compliance matrix with Art. 12, Art. 43 and
Art. 72 *absent*: each was the sole responsibility of an artefact the Verifier
escalated, and ``_derive_verdicts`` builds the matrix from the union of admitted,
insufficient, finding-bearing and gate-scoped articles — an escalated artefact is
in none of the four.  Fix 20 built the gate that closes this and wired it to
``unverified`` alone.

These tests fix the generalisation: the gate asks *did the Verifier admit this
artefact?* rather than naming one verdict, so every non-admitting verdict routes
its articles to ``INSUFFICIENT_EVIDENCE``.
"""
from __future__ import annotations

import pytest

from aaa.agents.tier1.phases.compliance_matrix.derive_verdicts import _derive_verdicts
from aaa.agents.tier1.phases.verification.logger import _VERDICT_ORDER
from aaa.agents.tier1.phases.verification.unadmitted import (
    UNADMITTED_VERDICTS,
    clear_unadmitted_insufficiency,
    gate_on_unadmitted,
)
from aaa.platform.state.admission import ADMITTED_VERDICTS

T15 = "T15_monitoring_logging_review"
T05 = "T05_art43_decision"
T09 = "T09_model_card"

#: The run's own case: T15 was escalated and is the only artefact accountable
#: for Art. 12 and Art. 72.
_T15_ARTICLES = ["Art.12", "Art.72"]


def _escalated(tid: str = T15, verdict: str = "escalate_hitl", **crit: object) -> dict:
    return {"verifier_critiques": {tid: {"verdict": verdict, **crit}},
            "phase_artefacts": {tid: {"uri": f"minio://x/{tid}"}}}


def _gate(state: dict, tid_articles: dict[str, list[str]], phase_id: str = "P5") -> list[str]:
    return gate_on_unadmitted(state, tid_articles, phase_id=phase_id,
                              phase_label=f"Phase {phase_id[-1]}")


# ── the gate is asked the admission question, not a verdict's name ───────────

def test_every_non_admitting_verdict_is_gated():
    """Derived from the verdict order, so a sixth verdict cannot slip past."""
    assert UNADMITTED_VERDICTS == frozenset(_VERDICT_ORDER) - ADMITTED_VERDICTS
    assert UNADMITTED_VERDICTS == {"unverified", "rerun", "escalate_hitl"}


@pytest.mark.parametrize("verdict", sorted(UNADMITTED_VERDICTS))
def test_an_unadmitted_artefacts_articles_are_unevidenced_not_absent(verdict):
    state = _escalated(verdict=verdict)

    assert _gate(state, {T15: _T15_ARTICLES}) == _T15_ARTICLES
    assert state["insufficient_evidence_articles"] == _T15_ARTICLES
    assert state["unadmitted_artefacts"][0]["verdict"] == verdict


@pytest.mark.parametrize("verdict", sorted(ADMITTED_VERDICTS))
def test_an_admitted_artefact_is_left_alone(verdict):
    state = _escalated(verdict=verdict)

    assert _gate(state, {T15: _T15_ARTICLES}) == []
    assert "unadmitted_artefacts" not in state
    assert "blocking_findings" not in state


def test_the_finding_names_the_verdict_and_the_verifiers_own_reason():
    state = _escalated(issues=["Rationale misstates Art. 43 §2", "second issue"])

    _gate(state, {T15: _T15_ARTICLES})

    description = state["blocking_findings"][0]["description"]
    assert "escalate_hitl" in description
    assert "Rationale misstates Art. 43 §2" in description
    assert state["blocking_findings"][0]["eu_ai_act_articles"] == _T15_ARTICLES


# ── the Q1 reproduction, end to end through the matrix ───────────────────────

def test_an_escalated_artefacts_articles_appear_in_the_delivered_matrix():
    """Art. 12 and Art. 72 read ABSENT in the delivered run; they now read a verdict."""
    state = _escalated()
    state.update({"blocking_findings": [], "compliance_matrix": {}, "scope_gate": {}})
    _gate(state, {T15: _T15_ARTICLES})

    _derive_verdicts(state)

    assert [state["compliance_matrix"].get(a) for a in _T15_ARTICLES] == [
        "INSUFFICIENT_EVIDENCE", "INSUFFICIENT_EVIDENCE"]


def test_an_article_another_artefact_still_admits_keeps_its_evidence_listed():
    """The gate qualifies the article; it does not erase the evidence under it.

    The second artefact used to be `T09_model_card` citing Art. 43. A model card
    evidences transparency and accuracy, not conformity assessment, and fix 50
    refuses a citation outside the artefact's contract — so the fixture now uses
    `T18_audit_report`, which really is accountable for Art. 43.
    """
    T18 = "T18_audit_report"
    state = _escalated(T05)
    state["verifier_critiques"][T18] = {"verdict": "accept",
                                        "article_citations": ["Art.43"]}
    state["phase_artefacts"][T18] = {"uri": "minio://x/T18"}
    state.update({"blocking_findings": [], "compliance_matrix": {}, "scope_gate": {}})
    _gate(state, {T05: ["Art.43"], T18: ["Art.43"]}, phase_id="P1")

    _derive_verdicts(state)

    assert state["compliance_matrix"]["Art.43"] == "INSUFFICIENT_EVIDENCE"
    assert state["article_evidence"]["Art.43"]["supporting_template_ids"] == [T18]


# ── idempotent under the Orchestrator's re-dispatch (Q8) ─────────────────────

def test_a_re_dispatched_phase_records_the_gate_once():
    state = _escalated()

    _gate(state, {T15: _T15_ARTICLES})
    assert _gate(state, {T15: _T15_ARTICLES}) == []

    assert len(state["unadmitted_artefacts"]) == 1
    assert len(state["blocking_findings"]) == 1
    assert state["insufficient_evidence_articles"] == _T15_ARTICLES


def test_a_re_dispatch_that_admits_the_artefact_releases_its_articles():
    state = _escalated()
    _gate(state, {T15: _T15_ARTICLES})

    state["verifier_critiques"][T15]["verdict"] = "accept_with_notes"
    assert _gate(state, {T15: _T15_ARTICLES}) == []

    assert state["insufficient_evidence_articles"] == []
    assert state["unadmitted_artefacts"] == []
    assert state["blocking_findings"] == []


def test_a_release_leaves_an_article_a_low_confidence_phase_still_holds():
    state = _escalated()
    _gate(state, {T15: _T15_ARTICLES})
    state["low_confidence_phases"] = [{"phase_id": "P5", "articles": ["Art.12"]}]

    state["verifier_critiques"][T15]["verdict"] = "accept"
    _gate(state, {T15: _T15_ARTICLES})

    assert state["insufficient_evidence_articles"] == ["Art.12"]


# ── and the human reviewer can still release it ──────────────────────────────

def test_every_gated_verdict_reaches_the_human_review_packet():
    """A gate the reviewer cannot see is a gate that can never be released."""
    from aaa.tools.hitl_review import _HITL_VERDICTS

    assert UNADMITTED_VERDICTS <= _HITL_VERDICTS


def test_a_human_who_admits_an_escalated_artefact_releases_its_articles():
    state = _escalated()
    _gate(state, {T15: _T15_ARTICLES})

    state["verifier_critiques"][T15]["verdict"] = "accept"

    assert clear_unadmitted_insufficiency(state) == _T15_ARTICLES
    assert state["insufficient_evidence_articles"] == []
