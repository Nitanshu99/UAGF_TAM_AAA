"""The wizard's contract with intake, after the pre-fill agent left the path.

The wizard used to run ``DocIntelligenceAgent`` on every upload: it indexed the
documents *and* spent an LLM call reading Stage A/B values out of them. Only the
indexing is load-bearing — the audit runs on what the customer confirms in the
form, and the collection built at upload time is the only route free-form
technical documentation takes into the phases' retrieval.

These tests pin what has to stay true now that only the indexing happens here.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from aaa.ui.wizard import live_view, pipeline
from aaa.ui.wizard.step1 import actions
from aaa.ui.wizard.step3 import checklist


class _Session(dict):
    """Enough of ``st.session_state`` for the upload bookkeeping."""


@pytest.fixture(name="session")
def _session(monkeypatch: pytest.MonkeyPatch) -> _Session:
    state = _Session()
    monkeypatch.setattr(actions, "st", SimpleNamespace(session_state=state))
    return state


# --- the model and the datasets must not be asked for twice ------------------

def test_a_step_one_model_upload_counts_towards_stage_b(session: _Session) -> None:
    """Uploaded once at step 1, it is the Stage B artefact — not just corpus.

    Before this, the file was indexed for retrieval and then silently dropped:
    ``s3_b_uris`` stayed empty, so Art. 15 and the fairness suite reported
    INSUFFICIENT_EVIDENCE unless the customer happened to upload the identical
    file a second time on the review page.
    """
    actions._claim_stage_b_uri("model_artifact_uri", "minio://x/model.pkl")
    assert session["s3_b_uris"] == {"model_artifact_uri": "minio://x/model.pkl"}


def test_a_later_upload_is_not_clobbered_by_the_earlier_one(session: _Session) -> None:
    """Step 3 replaces what step 1 supplied, never the other way round."""
    session["s3_b_uris"] = {"model_artifact_uri": "minio://x/replacement.pkl"}
    actions._claim_stage_b_uri("model_artifact_uri", "minio://x/original.pkl")
    assert session["s3_b_uris"]["model_artifact_uri"] == "minio://x/replacement.pkl"


def test_datasets_map_to_training_then_evaluation() -> None:
    """The order the two dataset slots are filled in is the declared one."""
    assert actions._DATASET_FIELDS == ("training_dataset_uri", "evaluation_dataset_uri")


def test_the_form_is_told_no_extraction_was_attempted() -> None:
    """'not_attempted' is not one of the four M23 failure causes.

    Those four all mean "we tried to read your documents and could not", and
    each carries an apology. None of them is true any more, and telling a
    customer their documents failed to parse when nothing tried to parse them
    is the exact error M23 was raised to stop.
    """
    assert actions._NO_EXTRACTION["extraction_status"] == "not_attempted"
    assert actions._NO_EXTRACTION["field_confidence"] == {}
    assert actions._NO_EXTRACTION["missing_fields"] == []


# --- indexing must survive its own failures ----------------------------------

def test_no_documents_is_not_an_ingest_failure() -> None:
    """Continuing without uploads is a supported route, not an error."""
    result = pipeline.ingest_documents("eng-x", [], store=None)  # type: ignore[arg-type]
    assert result == {"chunks_indexed": 0, "sources": [], "error": None}


def test_an_ingest_failure_is_reported_not_raised(monkeypatch: pytest.MonkeyPatch) -> None:
    """A customer mid-wizard must not lose the engagement to a Qdrant outage."""
    from aaa.tools import client_doc_ingest as module

    def _boom(*_args, **_kwargs):
        raise module.ClientDocIngestError("qdrant unreachable")

    monkeypatch.setattr(module, "client_doc_ingest", _boom)
    result = pipeline.ingest_documents("eng-x", ["minio://a"], store=None)  # type: ignore[arg-type]
    assert result["chunks_indexed"] == 0
    assert "qdrant unreachable" in result["error"]


# --- the checklist and the gate read the same report -------------------------

def _report(scores: dict[str, tuple[float, float]], total: float):
    """Build a CompletenessReport-shaped stub."""
    from aaa.tools.intake_completeness_calculator.section_weights import SectionScore
    return SimpleNamespace(
        score=total,
        section_scores={k: SectionScore(score=s, weight=w, label=f"Annex IV §{k}")
                        for k, (s, w) in scores.items()})


def test_gaps_rank_by_points_still_available_not_by_section_order() -> None:
    """§1 is worth 0.20 and §8 is worth 0.05; effort should go to §1 first."""
    gaps = checklist._gaps(_report({"1": (0.0, 0.20), "8": (0.0, 0.05),
                                    "4": (0.0, 0.15)}, 0.0))
    assert [g[0] for g in gaps] == [1, 4, 8]


def test_a_part_filled_section_offers_only_what_is_left() -> None:
    """Half of §1 done is ten points remaining, not twenty."""
    gaps = checklist._gaps(_report({"1": (0.5, 0.20)}, 0.1))
    assert gaps[0][2] == pytest.approx(0.10)


def test_a_complete_section_is_not_listed_as_a_gap() -> None:
    assert checklist._gaps(_report({"1": (1.0, 0.20)}, 0.2)) == []


def test_every_scored_section_has_customer_facing_words() -> None:
    """A gap the customer cannot name is a gap they cannot close."""
    from aaa.tools.intake_completeness_calculator.section_weights import SECTION_WEIGHTS

    for section in SECTION_WEIGHTS:
        label, where = checklist.SECTION_LABELS[section]
        assert label and not label.startswith("Annex IV")
        assert where in {"Your system", "The dossier", "Documents"}


def test_live_completeness_still_agrees_with_the_full_report() -> None:
    """The meter and the checklist must never disagree about the score."""
    stage_a = {"declared_modality": "tabular"}
    stage_b = {"general_description": "x" * 60, "model_type": "XGBoost"}
    report = live_view.live_report(stage_a, stage_b)
    assert report is not None
    assert live_view.live_completeness(stage_a, stage_b) == pytest.approx(report.score)
