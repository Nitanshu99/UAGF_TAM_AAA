"""Fix 47 — fairness cites the articles that require it (finding R15).

**The system's own Verifier found this, not the assessment.** Case 05 #017,
graded `critical` / `material`:

    "Art. 15§1 concerns accuracy, robustness and cybersecurity only.
     Non-discrimination bias examination is mandated by Art. 10§2(f) (and Art. 9
     risk management). The compliance note 'Non-discrimination assessed per
     Art. 15 §1' is a false compliance claim under the wrong article."

The mis-attribution had reached the compliance matrix of all five cases.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aaa.agents.tier1.phases.compliance_matrix.logger import _TEMPLATE_ARTICLES
from aaa.agents.tier1.phases.node_stubs.logger import TEMPLATE_ARTICLES
from aaa.agents.tier2.output_fairness.articles import EVIDENCED_ARTICLES, FINDING_ARTICLES

T12, T13 = "T12_output_fairness_report", "T13_output_sampling_log"
SCHEMA_DIRS = ("templates",
               "packages/uagf_tam_templates/src/uagf_tam_templates/schemas")


# --------------------------------------------------------------------------- #
# the attribution itself
# --------------------------------------------------------------------------- #

def test_a_fairness_finding_cites_the_articles_that_require_the_examination():
    assert FINDING_ARTICLES == ["Art.10§2(f)", "Art.9"]


def test_art_15_1_is_not_a_non_discrimination_obligation():
    """It governs accuracy, robustness and cybersecurity, and nothing else."""
    assert "Art.15§1" not in FINDING_ARTICLES
    assert "Art.15§1" not in EVIDENCED_ARTICLES
    assert "Art.15" not in FINDING_ARTICLES


def test_a_phase_4_evidence_gap_holds_back_only_what_phase_4_evidences():
    """A finding names every article it bears on; a gap names only the contract's.

    Art. 9 is assessed in Phase 5 through the CGSA payload. A fairness gap that
    could mark it unevidenced would let Phase 4 disclaim an article another phase
    had evidence for — and Art. 9 is a core high-risk article, so that reaches
    the opinion.
    """
    assert EVIDENCED_ARTICLES == ["Art.10§2(f)"]
    assert "Art.9" in FINDING_ARTICLES and "Art.9" not in EVIDENCED_ARTICLES


# --------------------------------------------------------------------------- #
# three maps that disagreed now agree
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("tid", [T12, T13])
def test_every_article_map_agrees_on_what_these_artefacts_evidence(tid):
    assert _TEMPLATE_ARTICLES[tid] == ["Art.10§2(f)"]
    assert TEMPLATE_ARTICLES[tid] == ["Art.10§2(f)"]


def test_the_phase_contract_agrees_with_the_maps():
    source = Path("aaa/agents/tier1/phases/phase_runners/phase/p4.py").read_text()
    contract = source.split("tid_articles={", 1)[1].split("}", 1)[0]
    assert '"T12_output_fairness_report": ["Art.10§2(f)"]' in contract
    assert '"T13_output_sampling_log": ["Art.10§2(f)"]' in contract
    assert "Art.15§1" not in contract


def test_an_admitted_fairness_artefact_no_longer_passes_art_15_or_art_50():
    """Case 05 delivered `Art.50 = PASS` resting on an output sampling log."""
    for tid in (T12, T13):
        assert "Art.15" not in _TEMPLATE_ARTICLES[tid]
        assert "Art.50" not in _TEMPLATE_ARTICLES[tid]


# --------------------------------------------------------------------------- #
# no template asserts a compliance claim under an article it has not checked
# --------------------------------------------------------------------------- #

def _t12(skipped: str | None = None, verdict: str | None = None) -> dict:
    """Build a real T12 from a real suite; *verdict* overrides the aggregate."""
    from aaa.agents.tier2.output_fairness.suite import run_fairness_suite
    from aaa.agents.tier2.output_fairness.t12 import build_t12
    from tests.unit.test_fairness_group_validity import _inputs
    inp = _inputs()
    suite = run_fairness_suite(inp)
    if verdict is not None:
        suite.overall_verdict = verdict
    return build_t12("eng-x", "tabular", inp, suite, skipped, "2026-09-03T00:00:00Z")


def test_t12_does_not_claim_an_examination_that_did_not_happen():
    note = _t12(skipped="no predictions available", verdict="NOT_TESTED")[
        "art10_2f_compliance_notes"]
    assert "was not performed" in note
    assert "performed per Art. 10 §2(f)" not in note


def test_t12_says_what_it_did_when_it_did_it():
    note = _t12()["art10_2f_compliance_notes"]
    assert "Bias examination performed per Art. 10 §2(f)" in note


def test_t12_attributes_to_art_9_without_asserting_conformity_with_it():
    note = _t12()["art9_compliance_notes"]
    assert "Art. 9" in note
    assert "is not asserted here" in note
    assert "art15_1_compliance_notes" not in _t12()


def test_t09_no_longer_asserts_a_risk_management_process_phase_3_never_checked():
    """Read the card the builder emits, not the file the sentence once lived in."""
    from aaa.agents.tier2.model_validator.t09 import build_t09

    t09 = build_t09("eng-x", {}, {}, "tabular", {}, "2026-09-14T00:00:00Z")
    assert "Subject to ongoing risk-management process" not in t09["ethical_considerations"]
    assert "is not evaluated here" in t09["ethical_considerations"]


def test_t13_inspects_for_bias_under_the_bias_article():
    source = Path("aaa/agents/tier2/output_fairness/t13/__init__.py").read_text()
    assert '"art10_2f_compliance_notes"' in source
    assert "art15_1_compliance_notes" not in source


# --------------------------------------------------------------------------- #
# both schema copies, including the descriptions that carried the same claim
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("base", SCHEMA_DIRS)
def test_neither_schema_copy_still_names_the_wrong_article(base):
    for name in (T12, T13):
        doc = json.loads((Path(base) / f"{name}.json").read_text())
        assert "art15_1_compliance_notes" not in doc["properties"]
        assert "Art. 15" not in doc["description"]


@pytest.mark.parametrize("base", SCHEMA_DIRS)
def test_both_schema_copies_carry_the_renamed_properties(base):
    t12 = json.loads((Path(base) / f"{T12}.json").read_text())["properties"]
    t13 = json.loads((Path(base) / f"{T13}.json").read_text())["properties"]
    assert "art9_compliance_notes" in t12
    assert "art10_2f_compliance_notes" in t12
    assert "art10_2f_compliance_notes" in t13


def test_t12_still_validates_against_its_schema():
    from aaa.tools.template_render.logger import _load_schema, _validate_payload
    assert _validate_payload(_t12(), _load_schema(T12), T12) == []
