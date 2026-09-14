"""An optional phase whose evidence the provider supplied must be dispatched.

Case 02 (a limited-risk forecaster) uploaded its model and both datasets, yet the
§6.2 catalogue marks Phases 3 and 4 optional for that tier and the Orchestrator
never dispatched an optional phase — the model was never scored.
"""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.orchestrator.react.coverage import pending_mandatory
from aaa.agents.tier1.phases.nodes.plan import node_plan
from aaa.tools.csp_solver.supplied import promote_supplied

UPLOADS = {"model_artifact_uri": "minio://eng/model.joblib",
           "evaluation_dataset_uri": "minio://eng/evaluation_dataset.csv"}


def _state(tier: str, stage_b: dict[str, Any], llm: bool = False) -> dict[str, Any]:
    """An engagement of *tier* whose Stage B dossier is *stage_b*."""
    return {"engagement_id": "eng-supplied", "risk_tier": tier,
            "modality": "llm" if llm else "tabular", "is_llm_or_agentic": llm,
            "annex_iii_mapping": [], "phase_artefacts": {},
            "client_submission": {"stage_b": stage_b}}


def test_uploaded_model_and_data_make_phases_3_and_4_mandatory() -> None:
    """The plan, its template expansion and the coverage guard all owe P3 and P4."""
    state = node_plan(_state("limited", UPLOADS))
    assert state["phase_plan"]["P3"] == "M" and state["phase_plan"]["P4"] == "M"
    assert state["phase_status"]["T09_model_card"] == "M"
    assert "model_artifact_uri" in state["phase_plan_rationale"]["P3"]
    state["phase_artefacts"] = {"T02_system_card": "u", "T06_datasheet_for_datasets": "u"}
    assert pending_mandatory(state, {}, cap=2) == "P3"


def test_without_uploads_the_catalogue_stands() -> None:
    """Nothing supplied, nothing promoted."""
    state = node_plan(_state("limited", {}))
    assert state["phase_plan"]["P3"] == "O" and state["phase_plan"]["P4"] == "O"
    assert "P3" not in state["phase_plan_rationale"]


def test_a_dataset_alone_does_not_owe_model_validation() -> None:
    """Phase 3 examines the model; data without a model does not make it runnable."""
    plan = {"P2": "O", "P3": "O", "P4": "O"}
    reasons = promote_supplied(_state("limited", {"training_dataset_uri": "minio://x.csv"}), plan)
    assert plan == {"P2": "M", "P3": "O", "P4": "O"} and set(reasons) == {"P2"}


def test_a_routing_skip_is_never_promoted() -> None:
    """``S`` for a generative-only system means no model of that kind exists."""
    plan = {"P3": "S", "P4": "S"}
    assert not promote_supplied(_state("minimal", UPLOADS, llm=True), plan)
    assert plan == {"P3": "S", "P4": "S"}


def test_a_minimal_risk_model_that_was_supplied_is_examined_voluntarily() -> None:
    """User decision T-075 (option A): the tier skip is opened under Art. 95, as observations."""
    plan = {"P3": "S", "P4": "S"}
    reasons = promote_supplied(_state("minimal", UPLOADS), plan)
    assert plan == {"P3": "M", "P4": "M"}
    assert "voluntarily (Art. 95)" in reasons["P3"] and "observations, not verdicts" in reasons["P3"]
    assert not promote_supplied(_state("prohibited", UPLOADS), {"P3": "S"})


def test_a_golden_set_makes_the_l_branch_mandatory() -> None:
    """A minimal-tier LLM with a golden set gets its answers scored."""
    state = node_plan(_state("minimal", {"golden_set_uri": "minio://eng/golden.json"}, llm=True))
    assert state["phase_plan"]["L"] == "M"
