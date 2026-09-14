"""Unit tests for :mod:`aaa.ui.wizard.collect.stage.b_meta` session-state resolution."""
from __future__ import annotations

from aaa.ui.wizard.collect.stage.b_meta import data_dictionary_block, model_meta_fields


def test_all_fields_from_new_widgets() -> None:
    """Column-aware widget keys resolve into every top-level S6 field."""
    state = {"s3_b_dd_target_sel": "credit_risk", "s3_b_dd_positive": "1",
             "s3_b_dd_sensitive_ms": ["age_group", "sex"],
             "s3_b_task_type": "binary_classification",
             "s3_b_model_format": "joblib", "s3_b_model_framework": "sklearn"}
    fields = model_meta_fields(state)
    assert fields == {"target_column": "credit_risk", "positive_label": "1",
                      "sensitive_feature_columns": ["age_group", "sex"],
                      "immutable_feature_columns": None,
                      "actionable_feature_columns": None,
                      "task_type": "binary_classification",
                      "model_format": "joblib", "model_framework": "sklearn",
                      "model_artifact_kind": None, "model_entrypoint": None}


def test_artifact_layout_fields_resolve() -> None:
    """A directory artefact carries its layout and entry point (fix F7)."""
    fields = model_meta_fields({"s3_b_model_artifact_kind": "directory",
                                "s3_b_model_entrypoint": "demandpulse_v3.0.joblib"})
    assert fields["model_artifact_kind"] == "directory"
    assert fields["model_entrypoint"] == "demandpulse_v3.0.joblib"


def test_actionability_columns_resolve() -> None:
    """DiCE constraints reach stage_b instead of being inferred from names."""
    fields = model_meta_fields({"s3_b_dd_immutable_ms": ["age", "credit_history"],
                                "s3_b_dd_actionable_ms": ["credit_amount"]})
    assert fields["immutable_feature_columns"] == ["age", "credit_history"]
    assert fields["actionable_feature_columns"] == ["credit_amount"]


def test_legacy_text_widgets_still_resolve() -> None:
    """Free-text keys (no dataset uploaded) parse commas and strip blanks."""
    state = {"s3_b_dd_target": " outcome ", "s3_b_dd_sensitive": "age, , sex "}
    fields = model_meta_fields(state)
    assert fields["target_column"] == "outcome"
    assert fields["sensitive_feature_columns"] == ["age", "sex"]


def test_unset_fields_are_none() -> None:
    """Empty session state yields ``None`` for every field."""
    fields = model_meta_fields({})
    assert all(value is None for value in fields.values())


def test_data_dictionary_block_drops_empty() -> None:
    """The legacy block contains only the non-empty data-dictionary entries."""
    block = data_dictionary_block({"s3_b_dd_target": "y"})
    assert block == {"target_column": "y"}
    assert data_dictionary_block({}) == {}


def test_ranking_pair_from_the_column_selects() -> None:
    """T-20260914-033: both ranking columns chosen reach data_dictionary.ranking."""
    block = data_dictionary_block({"s3_b_dd_target_sel": "relevant",
                                   "s3_b_dd_rank_query_sel": "query_id",
                                   "s3_b_dd_rank_position_sel": "rank"})
    assert block["ranking"] == {"query_column": "query_id", "rank_column": "rank"}


def test_ranking_pair_from_free_text() -> None:
    """Without a readable CSV header the free-text pair is used, stripped."""
    block = data_dictionary_block({"s3_b_dd_rank_query": " query_id ",
                                   "s3_b_dd_rank_position": "rank"})
    assert block == {"ranking": {"query_column": "query_id", "rank_column": "rank"}}


def test_a_partial_or_clashing_ranking_is_not_recorded() -> None:
    """One column alone, or one column twice, declares no ranking."""
    assert "ranking" not in data_dictionary_block({"s3_b_dd_rank_query_sel": "query_id"})
    assert "ranking" not in data_dictionary_block({"s3_b_dd_rank_query_sel": "query_id",
                                                   "s3_b_dd_rank_position_sel": "query_id"})


def test_the_collected_ranking_satisfies_the_dossier_schema() -> None:
    """What the wizard collects is what T01b's data_dictionary.ranking accepts."""
    import json
    import pathlib

    import jsonschema

    schema = json.loads(pathlib.Path("templates/T01b_annex_iv_dossier.json").read_text())
    block = data_dictionary_block({"s3_b_dd_target_sel": "y", "s3_b_dd_positive": "1",
                                   "s3_b_dd_rank_query_sel": "q",
                                   "s3_b_dd_rank_position_sel": "r"})
    jsonschema.validate(block, schema["properties"]["data_dictionary"])
