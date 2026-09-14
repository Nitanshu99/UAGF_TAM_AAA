"""A composite system must route the same whichever door it came through.

Case 06 is a ranking model beside a generative model. Submitted
whole through the API its Stage A carries ``component_modalities`` and the plan
plans Phases 3 and 4. Built by the wizard it carried only the scalar ``llm``,
the CSP pinned ``P3`` and ``P4`` to ``S``, and the audit returned 57.1 %
coverage with ``suitable_for_handoff: true`` and nothing saying model validation
and output fairness had never been attempted.

The last test here is the one that would have caught it: the two intake paths
agreeing is exactly what stopped being true.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from aaa.tools.csp_solver import solve_phase_plan
from aaa.ui.wizard.collect.components import discriminative_evidence
from aaa.ui.wizard.collect.modalities import derive_component_modalities

_MOCK = pathlib.Path("mock/06_mariposa_edu_gmbh")

#: What a ranking dossier reports — ranking metrics, no model file (synthetic values).
_RANKING_METRICS = {
    "precision_at_3": 0.61, "ndcg_at_5": 0.71,
    "baseline_precision_at_5": 0.41,
}


def _state(stage_a: dict) -> dict:
    """An AuditState shaped the way IntakeValidator builds one.

    ``declared_modality`` and ``is_llm_or_agentic`` are lifted to the top level
    beside the submission, which is what ``component_modalities()`` falls back
    to and what ``build_phase_csp`` reads — a fixture carrying them only inside
    ``client_submission`` routes as if no modality were declared at all.
    """
    modality = stage_a.get("declared_modality")
    return {"engagement_id": "eng-t", "risk_tier": "high",
            "declared_risk_tier": "high", "annex_iii_mapping": [],
            "special_category_data": False,
            "declared_modality": modality, "modality": modality,
            "is_llm_or_agentic": modality in {"llm", "agentic", "gpai"},
            "client_submission": {"stage_a": stage_a}}


# --- what the dossier shows -------------------------------------------------

def test_ranking_metrics_are_discriminative_evidence() -> None:
    """precision@k and nDCG@k are not things a pure LLM reports."""
    reasons = discriminative_evidence(
        {"accuracy_metrics": _RANKING_METRICS,
         "evaluation_dataset_uri": "minio://x/eval.csv"})
    assert reasons
    assert any("ranking/classification metrics" in r for r in reasons)


def test_a_data_dictionary_is_discriminative_evidence() -> None:
    """Naming a prediction target describes a discriminative model."""
    assert discriminative_evidence({"target_column": "hired"})
    assert discriminative_evidence({"sensitive_feature_columns": ["gender"]})


def test_generative_only_metrics_are_not() -> None:
    """No false positive on a system that genuinely is only a language model."""
    assert discriminative_evidence(
        {"accuracy_metrics": {"toxicity_rate": 0.01, "refusal_rate": 0.03}}) == []
    assert discriminative_evidence({}) == []


def test_metrics_are_read_from_the_wrapped_shape_too() -> None:
    """Stage B accepts a nested block; the signal must survive either shape."""
    assert discriminative_evidence(
        {"accuracy_metrics": {"accuracy_metrics": _RANKING_METRICS}})


def test_metrics_are_read_from_the_raw_json_the_form_holds() -> None:
    """The wizard carries this field as text until Stage B is assembled."""
    assert discriminative_evidence({"accuracy_metrics": json.dumps(_RANKING_METRICS)})
    assert discriminative_evidence({"accuracy_metrics": "not json"}) == []


# --- what the customer says wins -------------------------------------------

def test_saying_yes_declares_the_component_without_any_dossier_signal() -> None:
    parts = derive_component_modalities("llm", {}, True)
    assert [p["modality"] for p in parts] == ["llm", "nlp"]
    assert "Declared by the customer" in parts[1]["role"]


def test_saying_no_is_taken_at_their_word() -> None:
    """Asking and then overriding the answer would make the question a lie."""
    assert derive_component_modalities(
        "llm", {"accuracy_metrics": _RANKING_METRICS}, False) is None


def test_never_asked_falls_back_to_the_dossier() -> None:
    parts = derive_component_modalities("llm", {"target_column": "hired"}, None)
    assert parts is not None
    assert "Inferred from the dossier" in parts[1]["role"]


def test_a_discriminative_declaration_is_left_alone() -> None:
    """Only a generative system can carry a hidden second component."""
    assert derive_component_modalities("tabular", {"target_column": "x"}, True) is None


# --- the routing consequence ------------------------------------------------

def test_a_generative_only_declaration_still_skips_p3_p4() -> None:
    """The existing behaviour is correct for a real single-component LLM."""
    plan = solve_phase_plan(_state({"declared_modality": "llm"}))
    assert plan["P3"] == "S" and plan["P4"] == "S"


def test_a_derived_component_restores_model_and_fairness_phases() -> None:
    """The defect, stated as its repair."""
    parts = derive_component_modalities(
        "llm", {"accuracy_metrics": _RANKING_METRICS,
                "evaluation_dataset_uri": "minio://x/eval.csv"}, None)
    plan = solve_phase_plan(
        _state({"declared_modality": "llm", "component_modalities": parts}))
    assert plan["P3"] == "M" and plan["P4"] == "M"
    assert plan["L"] in ("M", "O")  # the generative branch is not lost


def test_deriving_a_component_can_only_add_obligations() -> None:
    """A false positive must audit more, never less."""
    from aaa.tools.csp_solver.catalogue import merge_requirements

    alone = merge_requirements(["llm"])
    both = merge_requirements(["llm", "nlp"])
    for var, status in alone.items():
        assert var in both and both[var] == status


# --- the parity test that would have caught it ------------------------------

@pytest.mark.skipif(not (_MOCK / "stage_a.json").is_file(),
                    reason="needs the case-06 mock bundle")
def test_the_wizard_and_the_api_route_case_06_the_same() -> None:
    """One case, two intake paths, one phase plan.

    The API stores ``stage_a.json`` verbatim; the wizard builds the declaration
    field by field. When those disagree about a system's components they
    disagree about which phases run — silently, because a skipped phase leaves
    no artefact to notice the absence of.
    """
    api_plan = solve_phase_plan(
        _state(json.loads((_MOCK / "stage_a.json").read_text(encoding="utf-8"))))

    stage_b = json.loads((_MOCK / "stage_b.json").read_text(encoding="utf-8"))
    wizard_stage_a = {"declared_modality": "llm"}
    parts = derive_component_modalities("llm", stage_b, None)
    if parts:
        wizard_stage_a["component_modalities"] = parts
    wizard_plan = solve_phase_plan(_state(wizard_stage_a))

    assert wizard_plan == api_plan, (
        f"wizard {wizard_plan} != api {api_plan} — the two intake paths "
        "disagree about which phases this engagement needs")
