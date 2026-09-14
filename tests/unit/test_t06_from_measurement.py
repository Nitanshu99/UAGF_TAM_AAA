"""T06 reports the dataset Phase 2 measured, and null for what nobody measured or declared.

Every engagement's T06 said ``num_instances: 0`` because the builder read a key no
contract defines, while Phase 2 had loaded the 600-row evaluation set
(T-20260913-009).
"""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from aaa.agents.tier2.data_auditor.t06 import build_t06, measure
from aaa.tools.missingness_scan import missingness_scan
from tests.unit.support.case06_like_dossier import SENSITIVE, STAGE_B, T01A, evaluation_frame

SCHEMA = json.loads(Path("templates/T06_datasheet_for_datasets.json").read_text(encoding="utf-8"))


def _t06(df=None) -> dict:
    measured = (measure(df, True, STAGE_B["evaluation_dataset_uri"], missingness_scan(df))
                if df is not None else None)
    return build_t06("eng-t", T01A, STAGE_B, {"stage_b": STAGE_B}, "2026-09-13T00:00:00Z",
                     measured=measured)


def _errors(t06: dict) -> list[str]:
    return [f"{list(e.path)}: {e.message}"
            for e in jsonschema.Draft202012Validator(SCHEMA).iter_errors(t06)]


def test_composition_is_what_phase_2_measured() -> None:
    """600 rows, 13 attributes besides the target, five declared sensitive features, the label named."""
    t06 = _t06(evaluation_frame())
    comp = t06["composition"]
    assert (comp["num_instances"], comp["num_features"]) == (600, 13)
    assert comp["sensitive_features"] == SENSITIVE and comp["has_labels"] is True
    assert "advanced" in comp["label_description"]
    assert comp["missing_data_present"] is False
    assert "minio://e/eval.csv" in t06["art10_compliance_notes"]
    assert not _errors(t06)


def test_no_dataset_is_null_not_zero() -> None:
    """Unknown counts are null, and the note says why."""
    t06 = _t06()
    comp = t06["composition"]
    assert comp["num_instances"] is None and comp["num_features"] is None
    assert comp["missing_data_present"] is None
    assert "No dataset could be loaded" in t06["art10_compliance_notes"]
    assert not _errors(t06)


def test_missing_cells_are_reported_from_the_scan() -> None:
    """A gap in the data is measured, not hardcoded away."""
    df = evaluation_frame()
    df.loc[:9, "sex"] = None
    comp = _t06(df)["composition"]
    assert comp["missing_data_present"] is True
    assert "sex" in comp["missing_data_description"]


def test_nothing_the_contract_does_not_carry_is_asserted() -> None:
    """Consent, preprocessing and labelling are unknown, not false."""
    t06 = _t06(evaluation_frame())
    assert t06["collection_process"]["consent_obtained"] is None
    pre = t06["preprocessing_cleaning_labelling"]
    assert pre["preprocessing_performed"] is None and pre["labelling_performed"] is None
