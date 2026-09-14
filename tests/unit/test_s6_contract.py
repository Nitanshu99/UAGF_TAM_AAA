"""Unit tests for the S6 field projection (fixes F8-F11, F15, findings S8-S15, S18-S19).

Hermetic by construction. An earlier version of this file read the five states
under ``data/customer/`` — a **gitignored** tree of run output — so it could not
run on a fresh clone, and the 2026-09-06 re-run changed two of its assertions by
producing better data. Logic is therefore tested against states built here;
the delivered tree is checked separately, and skipped when it is absent.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aaa.integrations.s6_contract import build_s6_fields
from aaa.integrations.s6_contract import vocabulary as vocab
from aaa.integrations.s6_contract.translate import (
    application_domain,
    primary_section,
    split_modality,
)

_FIXTURE = Path("tests/fixtures/customer_finclear/eng-01_finclear_gmbh_audit_state.json")
_DELIVERED = Path("data/customer")


def _fixture() -> dict:
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


def _entry(section: str, confidence: float, provenance: str = "phase1_verified") -> dict:
    return {"annex_iii_section": section, "confidence": confidence,
            "provenance": provenance, "section_title": "t", "use_case_marker": "m",
            "derogation_claimed": False}


# ── F8: modality and system_type are two different questions ────────────────

@pytest.mark.parametrize("declared,expected", [
    ("tabular", ("tabular", "traditional_ml")),
    ("time_series", ("time_series", "traditional_ml")),
    ("nlp", ("text", "traditional_ml")),
    ("cv", ("image", "traditional_ml")),
    ("llm", ("text", "llm")),
    ("agentic", ("text", "agentic")),
    ("gpai", ("multimodal", "llm")),
])
def test_every_internal_modality_splits_into_s6_values(declared, expected) -> None:
    """AAA's enum conflates two axes; both halves must land in S6's vocabulary."""
    modality, system_type = split_modality({"modality": declared})
    assert (modality, system_type) == expected
    assert modality in vocab.MODALITIES
    assert system_type in vocab.SYSTEM_TYPES


def test_unknown_modality_still_yields_a_usable_system_type() -> None:
    """``is_llm_or_agentic`` is the fallback it was always meant to be."""
    assert split_modality({"modality": "quantum", "is_llm_or_agentic": True}) == \
        ("unknown", "llm")
    assert split_modality({}) == ("unknown", "traditional_ml")


def test_llm_and_agentic_are_distinguished() -> None:
    """A bool cannot tell these apart, which is finding S14."""
    assert split_modality({"modality": "llm"})[1] == "llm"
    assert split_modality({"modality": "agentic"})[1] == "agentic"


# ── F10: application_domain ─────────────────────────────────────────────────

@pytest.mark.parametrize("section,domain", [
    ("1", "biometrics"), ("2", "critical_infrastructure"), ("3", "education"),
    ("4", "employment"), ("5", "essential_services"), ("6", "law_enforcement"),
    ("7", "migration"), ("8", "justice"),
])
def test_each_annex_iii_section_maps_to_its_domain(section, domain) -> None:
    """The mapping that existed nowhere in the codebase before F10 (S15)."""
    assert application_domain({"annex_iii_mapping": [_entry(section, 0.8)]}) == domain
    assert domain in vocab.APPLICATION_DOMAINS


def test_declared_sections_are_the_fallback() -> None:
    """Phase 1 may not have run; the client's declaration still resolves."""
    assert application_domain(
        {"annex_iii_mapping": [], "declared_annex_iii_sections": ["2"]}
    ) == "critical_infrastructure"


def test_no_section_in_scope_is_unknown_not_a_guess() -> None:
    """A limited-tier system with no Annex III section resolves to unknown."""
    assert application_domain({"annex_iii_mapping": [],
                               "declared_annex_iii_sections": []}) == "unknown"
    assert application_domain({}) == "unknown"


def test_primary_section_ranks_by_confidence_not_by_number() -> None:
    """LegalMind's real shape: §8 justice at 0.75 beside §1 biometrics at 0.675.

    Ranking by lowest section number would file a contract-drafting assistant
    under biometrics on the weaker of the two entries.
    """
    state = {"annex_iii_mapping": [_entry("8", 0.75, "client_declared"),
                                   _entry("1", 0.675)]}
    assert primary_section(state) == "8"
    assert application_domain(state) == "justice"


def test_rejected_entries_do_not_set_the_domain() -> None:
    """An entry Phase 1 refuted is not evidence of a domain."""
    state = {"annex_iii_mapping": [_entry("1", 0.9, "phase1_rejected"),
                                   _entry("4", 0.5)]}
    assert application_domain(state) == "employment"


def test_multiple_sections_are_reported_as_an_ambiguity() -> None:
    """S6's field is singular, so the collapse is named rather than hidden."""
    _, warnings = build_s6_fields(
        {"annex_iii_mapping": [_entry("8", 0.75), _entry("1", 0.675)]})
    assert any("application_domain is a single value" in w for w in warnings)


# ── F9: vocabulary conformance ──────────────────────────────────────────────

def test_unsupported_names_the_value_and_the_accepted_set() -> None:
    """A disagreement is reported, never coerced into false agreement."""
    message = vocab.unsupported("governance_verdict", "partially_compliant",
                                vocab.GOVERNANCE_VERDICTS)
    assert message and "partially_compliant" in message


def test_unsupported_ignores_absent_and_case_differences() -> None:
    """A missing value is a presence problem; casing is not a disagreement."""
    assert vocab.unsupported("modality", None, vocab.MODALITIES) is None
    assert vocab.unsupported("modality", "", vocab.MODALITIES) is None
    assert vocab.unsupported("modality", "TABULAR", vocab.MODALITIES) is None


@pytest.mark.parametrize("verdict", ["partially_compliant", "non_compliant"])
def test_aaa_governance_verdicts_outside_s6s_set_are_warned(verdict) -> None:
    """AAA's CGSA emits three labels; S6 accepts one of them (finding S13)."""
    _, warnings = build_s6_fields({"cgsa_governance_verdict": verdict})
    assert any("governance_verdict" in w and verdict in w for w in warnings)


def test_the_committed_fixture_carries_no_vocabulary_warning() -> None:
    """A healthy, backfilled state projects cleanly onto S6's vocabulary."""
    fields, warnings = build_s6_fields(_fixture())
    assert [w for w in warnings if "outside the S6 accepted set"] == []
    assert fields["modality"] in vocab.MODALITIES
    assert fields["task_type"] in vocab.TASK_TYPES
    assert fields["model_artifact_kind"] in vocab.ARTIFACT_KINDS


# ── The S4 sheet's own key shape, and F11 ───────────────────────────────────

def test_domain_scores_are_keyed_by_domain_name() -> None:
    """The sheet says ``key = domain_name``; ``cgsa_domain_scores`` says ``D1 …``."""
    fields, _ = build_s6_fields({"cgsa_payload": {"domains": [
        {"domain_id": "D1", "domain_name": "Risk Management", "domain_score": 3.5}]}})
    assert fields["domain_scores"] == {"Risk Management": 3.5}


def test_missing_cgsa_yields_empty_domain_scores() -> None:
    """A run whose Phase 5 never ingested CGSA has nothing to key."""
    fields, _ = build_s6_fields({"cgsa_payload": None})
    assert fields["domain_scores"] == {}
    assert fields["csp_satisfied"] is None


def test_sensitive_feature_groups_travel_beside_the_column_names() -> None:
    """F11: how an attribute was grouped, not just that it was named."""
    fields, _ = build_s6_fields({"sensitive_feature_groups": [
        {"attribute": "age", "binned": True, "group_count": 5,
         "smallest_group_size": 49, "tested": True}]})
    assert fields["sensitive_feature_groups"][0]["attribute"] == "age"
    assert fields["sensitive_feature_groups"][0]["binned"] is True


def test_projection_is_json_serialisable() -> None:
    """It ships inside the hand-off envelope, so it must serialise."""
    fields, _ = build_s6_fields(_fixture())
    assert json.loads(json.dumps(fields, default=str))["provider_name"] == "FinClear GmbH"


# ── The delivered tree, when there is one ───────────────────────────────────

@pytest.mark.skipif(not _DELIVERED.is_dir(), reason="no delivered run output present")
def test_delivered_states_carry_no_unsupported_model_value() -> None:
    """Every re-run deliverable projects onto S6's model vocabulary.

    ``governance_verdict`` is excluded: AAA emits three labels and S6 accepts a
    different four, which is finding S13 and is owned by S6.
    """
    states = sorted(_DELIVERED.glob("*/eng-0*_audit_state.json"))
    if not states:
        pytest.skip("delivered tree present but empty")
    for path in states:
        _, warnings = build_s6_fields(json.loads(path.read_text(encoding="utf-8")))
        offenders = [w for w in warnings if "outside the S6 accepted set" in w
                     and not w.startswith("governance_verdict")]
        assert offenders == [], f"{path.name}: {offenders}"


# ── F15 (S19): sensitive_feature_columns is [] + a reason, never bare null ─

def test_declared_columns_pass_through_with_no_reason() -> None:
    """A case with real columns needs no explanation."""
    fields, _ = build_s6_fields({"client_submission": {"stage_b": {
        "sensitive_feature_columns": ["age", "sex"]}}})
    assert fields["sensitive_feature_columns"] == ["age", "sex"]
    assert fields["sensitive_feature_columns_skip_reason"] is None


def test_unscheduled_phase_4_names_the_phase_plan() -> None:
    """A limited-risk case where Phase 4 never ran (case 02's shape)."""
    fields, _ = build_s6_fields({"phase_plan": {"P4": "O"}, "phase_artefacts": {}})
    assert fields["sensitive_feature_columns"] == []
    assert "not run" in fields["sensitive_feature_columns_skip_reason"]
    assert "'O'" in fields["sensitive_feature_columns_skip_reason"]


def test_ran_but_unscoped_reuses_the_recorded_finding() -> None:
    """A case where Phase 4 ran and left its own reason (case 03's shape)."""
    state = {
        "phase_artefacts": {"T12_output_fairness_report": {"uri": "x"}},
        "blocking_findings": [{"finding_id": "P3-DATADICT",
                               "description": "No sensitive columns could be inferred."}],
    }
    fields, _ = build_s6_fields(state)
    assert fields["sensitive_feature_columns"] == []
    assert fields["sensitive_feature_columns_skip_reason"] == \
        "No sensitive columns could be inferred."


def test_ran_with_no_finding_at_all_still_gets_a_reason() -> None:
    """Never a bare null: even the fallback path names something."""
    state = {"phase_artefacts": {"T12_output_fairness_report": {"uri": "x"}}}
    fields, _ = build_s6_fields(state)
    assert fields["sensitive_feature_columns"] == []
    assert fields["sensitive_feature_columns_skip_reason"]


def test_never_emits_null_for_the_columns_field() -> None:
    """The sheet's own contract: empty list, never absent or null."""
    for state in ({}, {"client_submission": {"stage_b": {
                       "sensitive_feature_columns": None}}}):
        fields, _ = build_s6_fields(state)
        assert fields["sensitive_feature_columns"] == []
        assert isinstance(fields["sensitive_feature_columns"], list)
