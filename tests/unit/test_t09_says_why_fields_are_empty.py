"""T09 carries the reason for each empty field (T-20260914-028, case 06 on MiniMax)."""
from __future__ import annotations

from aaa.agents.tier2.model_validator.t09 import build_t09
from aaa.tools.template_render.logger import _load_schema, _validate_payload

_CASE_06 = {"model_access_mode": "not_provided", "training_data_description": "400 ranked rows",
            "evaluation_dataset_uri": "mock/06/datasets/evaluation_dataset.csv",
            "accuracy_metrics": {"precision_at_5": 0.58}}


def _card() -> dict:
    """A card for a hosted system whose model was not supplied and nothing was measured."""
    declared = {"source": "stage_b.accuracy_metrics", "verified": False,
                "values": {"precision_at_5": 0.58}}
    return build_t09("eng-06", {"system_name": "Ranker"}, _CASE_06, "llm",
                     {"primary_metric": "not measured", "metrics": {}}, "2026-09-14T00:00:00Z",
                     declared=declared)


def test_nothing_measured_names_no_metric_and_says_why() -> None:
    """No placeholder in the name field; the reason names the access mode and the supplied set."""
    performance = _card()["performance_metrics"]
    assert performance["primary_metric"] is None
    assert "model_access_mode 'not_provided'" in performance["not_measured_reason"]
    assert "evaluation_dataset.csv" in performance["not_measured_reason"]


def test_null_model_fields_carry_their_reason() -> None:
    """Architecture and training nulls are explained, not silent."""
    card = _card()
    for section in (card["architecture"], card["training_regime"]):
        assert "no model was supplied" in section["unrecorded_reason"]
    assert "framework" in card["architecture"]["unrecorded_reason"]


def test_the_limitation_states_the_real_cause() -> None:
    """Not "rerun against a live evaluation set" beside a supplied evaluation set."""
    limits = " ".join(_card()["known_limitations"])
    assert "live evaluation set" not in limits
    assert "Performance was not measured: no model was supplied" in limits
    assert "declared metrics are reported unverified" in limits


def test_the_card_validates_against_t09() -> None:
    """The new reason fields are in both schema copies."""
    assert not _validate_payload(_card(), _load_schema("T09_model_card"), "T09_model_card")
