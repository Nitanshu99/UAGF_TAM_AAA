"""T06 quotes the documents about the dataset it describes, or stays null.

Split from test_artefacts_quote_provider_documents.py (T-20260913-100); the
grounded answers come from the provider's documents (T-20260913-032/035/041).
"""
from __future__ import annotations

from aaa.agents.tier2.data_auditor.dataset import dataset_role, dataset_uri_of
from aaa.agents.tier2.data_auditor.t06 import build_t06, t06_questions
from aaa.platform.evidence.contract import artefact_schema_errors
from aaa.tools.document_evidence import DOSSIER
from tests.unit.support.case06_like_dossier import STAGE_B, T01A
from tests.unit.support.provider_documents import NOW, ev


def test_t06_quotes_the_documents_about_the_dataset_it_describes() -> None:
    """T06 quotes the documents about the dataset it describes."""
    found = {
        "acquisition": ev("Evaluation set: 400 rows drawn from the decision log 2025-03-01 to "
                           "2025-10-31, pseudonymised.", f"{DOSSIER}training_data_description"),
        "timeframe": ev("Evaluation set: 400 rows drawn from the decision log 2025-03-01 to "
                         "2025-10-31, pseudonymised.", f"{DOSSIER}training_data_description"),
        "preprocessing": ev("Evaluation set: 400 rows, pseudonymised."),
        "labelling": ev("Ground truth: the reviewer decision recorded in the audit trail."),
    }
    t06 = build_t06("eng", T01A, STAGE_B, {"stage_b": STAGE_B}, NOW, found=found)
    collection = t06["collection_process"]
    assert collection["acquisition_method"].startswith(
        "Provider statement (Annex IV dossier, training_data_description)")
    assert collection["collection_timeframe"] == (
        "2025-03-01 to 2025-10-31 (Annex IV dossier, training_data_description)")
    assert collection["consent_obtained"] is None
    assert collection["consent_mechanism"].startswith("Not declared")
    pre = t06["preprocessing_cleaning_labelling"]
    assert pre["preprocessing_performed"] is True and pre["labelling_performed"] is True
    assert "acquisition, timeframe, preprocessing, labelling" in t06["art10_compliance_notes"]
    assert not artefact_schema_errors("T06_datasheet_for_datasets", t06)


def test_t06_asserts_no_distribution_or_plan_nobody_declared() -> None:
    """T06 asserts no distribution or plan nobody declared."""
    t06 = build_t06("eng", T01A, STAGE_B, {"stage_b": STAGE_B}, NOW)
    assert t06["distribution"]["distribution_method"].startswith("Not declared")
    assert t06["maintenance"]["update_plan"].startswith("Not declared")
    assert t06["collection_process"]["acquisition_method"].startswith("Not declared")
    assert t06["preprocessing_cleaning_labelling"]["preprocessing_performed"] is None


def test_t06_questions_name_the_dataset_in_its_role() -> None:
    """T06 questions name the dataset in its role."""
    assert dataset_role(STAGE_B, {}) == "evaluation"
    assert dataset_uri_of(STAGE_B, {}) == "minio://e/eval.csv"
    assert dataset_role({}, {"dataset_uri": "minio://e/x.csv"}) is None
    acquisition = t06_questions("evaluation")[0]
    assert acquisition.key == "acquisition" and "evaluation set" in acquisition.subject
    # No declared field describes the evaluation set: its sentences must name it (T-097).
    assert not acquisition.subject_fields
