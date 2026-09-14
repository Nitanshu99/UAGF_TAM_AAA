"""T06 describes the dataset Phase 2 measured, not the one a description names.

Split from test_artefacts_quote_provider_documents.py (T-20260913-100).
"""
from __future__ import annotations

from aaa.agents.tier2.data_auditor.t06 import build_t06
from aaa.platform.evidence.contract import artefact_schema_errors
from tests.unit.support.case06_like_dossier import STAGE_B, T01A
from tests.unit.support.provider_documents import NOW


def test_t06_answers_subpopulation_impact_from_the_measured_labels() -> None:
    """T06 answers subpopulation impact from the measured labels."""
    from aaa.tools.label_disparity import label_disparity
    from tests.unit.support.case06_like_dossier import evaluation_frame

    frame = evaluation_frame()
    frame["advanced"] = [1 if (i % 3 == 0 or frame["sex"][i] == frame["sex"][0]) else 0
                                      for i in range(len(frame))]
    bias = label_disparity(frame, "advanced", 1, ["sex"])
    t06 = build_t06("eng", T01A, STAGE_B, {"stage_b": STAGE_B}, NOW, label_bias=bias)
    impact = t06["uses"]["impact_on_subpopulations"]
    assert impact is not None and "Measured in Phase 2" in impact and "sex" in impact
    assert build_t06("eng", T01A, STAGE_B, {"stage_b": STAGE_B}, NOW)["uses"][
        "impact_on_subpopulations"] is None
    assert not artefact_schema_errors("T06_datasheet_for_datasets", t06)


def test_t06_does_not_let_the_training_description_stand_for_the_measured_set() -> None:
    """FinClear: '1000 instances' beside num_instances 700 — two datasets in one sentence."""
    from aaa.agents.tier2.data_auditor.t06 import measure
    from aaa.tools.missingness_scan import missingness_scan
    from tests.unit.support.case06_like_dossier import evaluation_frame

    frame = evaluation_frame()
    measured = measure(frame, True, STAGE_B["evaluation_dataset_uri"], missingness_scan(frame))
    comp = build_t06("eng", T01A, STAGE_B, {"stage_b": STAGE_B}, NOW, measured=measured)["composition"]
    assert comp["instances_type"].startswith("Dataset examined: minio://e/eval.csv (600 rows")
    assert "a different dataset" in comp["instances_type"]
