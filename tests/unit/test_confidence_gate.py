"""Finding F5 — a reported confidence must be read as reported, and must count.

Two defects met in one line of ``run_phase_with_verification``:

    confidence = float(report.get("confidence", default_confidence) or default_confidence)

``0.0 or 0.9`` is ``0.9``, so the DataAuditor's ``confidence: 0.0`` at call #009
was recorded as 0.9 — the inversion of the signal.  And it would not have
mattered either way: the number's only consumer was a note string, so a phase
could close saying it was not confident and still contribute a nominally
complete artefact that the compliance matrix read as evidence.

These tests pin the read, the consequence, and the path from a doubted phase to
the disclaimer that fix 6 gave the audit.
"""
from __future__ import annotations

import asyncio
import importlib

from aaa.agents.tier1.phases.verification.confidence import (
    CONFIDENCE_FLOOR,
    gate_on_confidence,
    read_confidence,
)
from aaa.platform.prompt_registry import load_prompt
from aaa.platform.prompt_registry.prompt.path import _AGENT_SECTION_PATTERNS

_PHASE_2 = {"T06_datasheet_for_datasets": ["Art.10"],
            "T07_data_quality_report": ["Art.10"],
            "T08_special_category_data_log": ["Art.10§5"]}


def _gate(state: dict, confidence: float, tids: dict | None = None) -> list[str]:
    return gate_on_confidence(state, tids if tids is not None else _PHASE_2, confidence,
                              phase_id="P2", phase_label="Phase 2 DataAuditor")


# --------------------------------------------------------------------------- #
# reading the number
# --------------------------------------------------------------------------- #

def test_zero_confidence_is_not_read_as_the_default():
    """The F5 inversion: call #009 reported 0.0 and was recorded as 0.9."""
    report = {"confidence": 0.0}

    assert float(report.get("confidence", 0.9) or 0.9) == 0.9, "precondition: the old read"
    assert read_confidence(report, 0.9) == 0.0


def test_a_reported_value_is_kept_verbatim():
    """Attempt 1 at call #004 reported 0.3; the audit trail must say 0.3."""
    assert read_confidence({"confidence": 0.3}, 0.85) == 0.3


def test_the_default_applies_only_when_no_value_was_reported():
    """`default_confidence` stands in for silence, not for doubt."""
    assert read_confidence({}, 0.85) == 0.85
    assert read_confidence({"confidence": None}, 0.85) == 0.85
    assert read_confidence(None, 0.85) == 0.85


def test_a_non_numeric_confidence_falls_back_rather_than_raising():
    """A malformed field must not crash a phase that otherwise succeeded."""
    assert read_confidence({"confidence": "high"}, 0.85) == 0.85


def test_an_out_of_range_confidence_is_clamped():
    """The contract is 0.0–1.0; a model that ignores it cannot buy extra credit."""
    assert read_confidence({"confidence": 4}, 0.85) == 1.0
    assert read_confidence({"confidence": -2}, 0.85) == 0.0


# --------------------------------------------------------------------------- #
# the consequence
# --------------------------------------------------------------------------- #

def test_low_confidence_marks_the_phase_articles_insufficient():
    """A phase its own author does not stand behind is not evidence."""
    state: dict = {}
    newly = _gate(state, 0.0)

    assert newly == ["Art.10", "Art.10§5"]
    assert state["insufficient_evidence_articles"] == ["Art.10", "Art.10§5"]


def test_confidence_at_the_floor_is_admitted():
    """The floor is a floor, not a threshold to clear."""
    state: dict = {}
    assert _gate(state, CONFIDENCE_FLOOR) == []
    assert _gate(state, 0.85) == []
    assert "insufficient_evidence_articles" not in state


def test_the_gate_records_what_it_did_and_why():
    """A disclaimer traceable to self-reported doubt must be readable as such."""
    state: dict = {}
    _gate(state, 0.2)

    entry = state["low_confidence_phases"][0]
    assert entry["phase_id"] == "P2"
    assert entry["confidence"] == 0.2
    assert entry["floor"] == CONFIDENCE_FLOOR
    assert entry["articles"] == ["Art.10", "Art.10§5"]


def test_report_templates_are_not_gated():
    """T17/T18 summarise an already-assessed state (the `_REPORT_TIDS` rule)."""
    state: dict = {}
    newly = _gate(state, 0.0, {"T17_compliance_matrix": ["Art.17"],
                               "T18_audit_report": ["Art.43", "Annex_IV"]})

    assert newly == []
    assert state.get("insufficient_evidence_articles") in (None, [])
    assert state["low_confidence_phases"][0]["confidence"] == 0.0, (
        "the doubt is still recorded, it just does not unevidence the audit")


def test_an_article_already_recorded_is_not_recorded_twice():
    """`insufficient_evidence_articles` accumulates across phases and agents."""
    state: dict = {"insufficient_evidence_articles": ["Art.10"]}
    newly = _gate(state, 0.1)

    assert newly == ["Art.10§5"]
    assert state["insufficient_evidence_articles"] == ["Art.10", "Art.10§5"]


# --------------------------------------------------------------------------- #
# through the real verification loop
# --------------------------------------------------------------------------- #

def _run_phase(monkeypatch, report: dict, worst: str = "accept") -> dict:
    """Drive the real ``run_phase_with_verification`` over a scripted report."""
    mod = importlib.import_module(
        "aaa.agents.tier1.phases.verification.run_phase_with_verification")
    seen: dict = {}

    class _Agent:
        name = "DataAuditor"
        store = None

    async def _fake_run(agent, dispatch, state, timeout=180):
        return report, state

    async def _fake_verify(verifier, agent, dispatch, state, tid_articles,
                           phase_label, confidence, rerun_count):
        seen["confidence"] = confidence
        state["verifier_critiques"] = {
            tid: {"verdict": "accept", "issues": [], "article_citations": arts}
            for tid, arts in tid_articles.items()}
        return worst

    monkeypatch.setattr(mod, "run_agent_on_state", _fake_run)
    monkeypatch.setattr(mod, "_verify_artefacts", _fake_verify)
    monkeypatch.setattr(mod, "_get_verifier", lambda _rag=None: object())

    state: dict = {"engagement_id": "eng-01_finclear_gmbh", "verifier_critiques": {},
                   "phase_artefacts": {t: {"uri": f"minio://{t}"} for t in _PHASE_2}}
    asyncio.run(mod.run_phase_with_verification(
        _Agent(), {"phase_id": "P2", "evidence_uris": [], "declaration_summary": {}},
        state, _PHASE_2, "Phase 2 DataAuditor", default_confidence=0.85))
    state["_verifier_saw"] = seen.get("confidence")
    return state


def test_call_009_replayed_through_the_loop(monkeypatch):
    """The assessed Phase 2 closed at 0.0 and was admitted as 0.9 evidence."""
    state = _run_phase(monkeypatch, {"summary": "Retrieving Article 10 text.",
                                     "confidence": 0.0})

    assert state["_verifier_saw"] == 0.0, "the Verifier was told 0.9 in the assessed run"
    assert state["insufficient_evidence_articles"] == ["Art.10", "Art.10§5"]
    assert state["low_confidence_phases"][0]["phase_label"] == "Phase 2 DataAuditor"


def test_a_confident_phase_is_untouched_by_the_gate(monkeypatch):
    """The gate must not quietly unevidence ordinary, well-supported work."""
    state = _run_phase(monkeypatch, {"summary": "Art. 10 assessed.", "confidence": 0.82})

    assert state["_verifier_saw"] == 0.82
    assert state.get("insufficient_evidence_articles") in (None, [])
    assert state.get("low_confidence_phases") in (None, [])


def test_a_doubted_phase_reaches_the_matrix_as_insufficient_not_pass(monkeypatch):
    """The point of the gate: the matrix must not read doubt as conformity."""
    from aaa.agents.tier1.phases.compliance_matrix import node_compliance_matrix

    state = _run_phase(monkeypatch, {"summary": "Retrieving Article 10 text.",
                                     "confidence": 0.0})
    state.update({"phase_plan": {"P2": "M"}, "compliance_matrix": {},
                  "blocking_findings": [], "findings": []})
    matrix = node_compliance_matrix(state)["compliance_matrix"]
    assert matrix["Art.10"] == "INSUFFICIENT_EVIDENCE"

    # Control: the same admitted artefacts, with the gate's marking removed, are
    # what the assessed run had — and they PASS.
    state["insufficient_evidence_articles"] = []
    state["compliance_matrix"] = {}
    ungated = node_compliance_matrix(state)["compliance_matrix"]
    assert ungated["Art.10"] == "PASS", (
        "precondition: an accepted artefact from a zero-confidence phase used to pass")


def test_an_unevidenced_core_article_disclaims_even_on_healthy_kpis():
    """Fix 7 hands fix 6 its predicate: Art. 10 is a core high-risk article."""
    from aaa.agents.tier1.phases.compliance_matrix.compute_final_verdict import (
        _compute_final_verdict,
    )

    state = {"compliance_matrix": {"Art.10": "INSUFFICIENT_EVIDENCE", "Art.11": "PASS"},
             "completeness_score": 1.0, "regulatory_coverage_pct": 100.0,
             "intake_completeness_score": 1.0}

    assert _compute_final_verdict(state) == "DISCLAIMER_OF_OPINION"
    assert state["opinion_disclaimer"] is True, (
        "the disclaimer is derived from the article, not from a KPI shortfall")


def test_the_confidence_reaches_the_report_evidence_surface(monkeypatch):
    """A rescued or doubted run must be readable, not only machine-legible."""
    from aaa.agents.tier1.phases.phase_runners.phase6_declaration_summary import (
        _phase6_declaration_summary,
    )

    state = _run_phase(monkeypatch, {"summary": "s", "confidence": 0.1})
    surface = _phase6_declaration_summary(state, "eng-t", {})

    assert surface["low_confidence_phases"][0]["confidence"] == 0.1


# --------------------------------------------------------------------------- #
# the prompt half
# --------------------------------------------------------------------------- #

def test_every_phase_prompt_states_what_confidence_means():
    """The skeletons showed `"confidence": 0.0` with no semantics — and got 0.0."""
    for name in ("phase1_scope", "phase2_data", "phase3_model", "phase4_output",
                 "phase5_governance", "phase6_report", "uagf_tam_l", "cyber",
                 "privacy"):
        prompt = load_prompt(name)
        assert '"confidence": 0.0,' not in prompt, f"{name} still ships the placeholder"
        assert "INSUFFICIENT_EVIDENCE rather than assessed" in prompt, name


def test_no_prompt_at_all_ships_the_confidence_placeholder():
    """Agent 3 shipped it for want of a trailing comma.

    The assertion above matches `"confidence": 0.0,` — with the comma — so it
    reads a skeleton's interior fields and misses the value when `confidence`
    is the *last* one. Agent 3 was also outside the nine names it iterates.
    Both gaps let the same F5 placeholder stand in a live prompt; this test is
    over every prompt the registry can load, and is comma-blind.
    """
    for name in _AGENT_SECTION_PATTERNS:
        prompt = load_prompt(name)
        assert '"confidence": 0.0' not in prompt, f"{name} still ships the placeholder"


def test_agent_3_does_not_pre_fill_its_own_not_found_signal():
    """0.0 is Agent 3's "NOT FOUND IN CORPUS" token, and the skeleton showed it.

    Worse than the phase prompts' inert placeholder: this prompt's CONSTRAINTS
    give 0.0 a meaning, so a model mimicking the skeleton reports a corpus miss
    on a passage it did retrieve.
    """
    prompt = load_prompt("regulatory_rag")
    assert '"confidence": <0.0-1.0>' in prompt
    assert "0.0 is reserved for" in prompt
    assert "NOT FOUND IN CORPUS" in prompt
