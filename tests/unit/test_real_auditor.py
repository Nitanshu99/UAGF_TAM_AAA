"""
Tests for the "real auditor" behaviour: independent artefact loading, evidence-
grounded verdict derivation (FAIL / INSUFFICIENT_EVIDENCE / PASS), and the
auditor-opinion ladder including the disclaimer of opinion.

These lock in that absence of evidence never yields PASS, and that the compliance
matrix + opinion are derived from findings rather than rubber-stamped.
"""
from __future__ import annotations

import asyncio
import io
import os

import pytest

os.environ.setdefault("AAA_OFFLINE_MODE", "true")

from aaa.platform.artifact_loader import ArtifactUnavailable, infer_kind, load_artifact_from_uri
from aaa.platform.evidence import EvidenceStore
from aaa.tools.data_dictionary import resolve_data_dictionary


# ── artifact_loader ──────────────────────────────────────────────────────────

def _store_csv(store: EvidenceStore, eng: str) -> str:
    data = b"a,b,credit_risk\n1,x,1\n2,y,0\n"
    return store.store_file(eng, "customer_uploads", "evaluation_dataset_uri",
                            "eval.csv", "text/csv", data, "test")


def test_infer_kind():
    assert infer_kind("minio://e/p/model_v1.joblib") == "joblib"
    assert infer_kind("minio://e/p/eval.csv") == "csv"
    assert infer_kind("minio://e/p/doc.docx") == "docx"
    assert infer_kind("minio://e/p/blob.bin") == "bytes"


def test_loader_csv_roundtrip():
    store = EvidenceStore()
    uri = _store_csv(store, "eng-1")
    df = load_artifact_from_uri(uri, store, "csv")
    assert list(df.columns) == ["a", "b", "credit_risk"]
    assert len(df) == 2


def test_loader_joblib_roundtrip():
    joblib = pytest.importorskip("joblib")
    store = EvidenceStore()
    buf = io.BytesIO()
    joblib.dump({"hello": "world"}, buf)
    uri = store.store_file("eng-1", "customer_uploads", "model_artifact_uri",
                           "m.joblib", "application/octet-stream", buf.getvalue(), "test")
    obj = load_artifact_from_uri(uri, store, "joblib")
    assert obj == {"hello": "world"}


def test_loader_missing_raises():
    store = EvidenceStore()
    with pytest.raises(ArtifactUnavailable):
        load_artifact_from_uri("minio://eng-1/customer_uploads/nope.csv", store, "csv")
    with pytest.raises(ArtifactUnavailable):
        load_artifact_from_uri(None, store, "csv")


# ── data_dictionary ──────────────────────────────────────────────────────────

def test_data_dictionary_inference():
    cols = ["checking_status", "credit_amount", "age", "personal_status",
            "foreign_worker", "credit_risk"]
    dd = resolve_data_dictionary({}, cols)
    assert dd.target_column == "credit_risk"
    assert set(dd.sensitive_feature_columns) == {"age", "personal_status", "foreign_worker"}
    assert dd.assumptions  # undeclared → assumptions recorded
    assert dd.is_usable()


def test_data_dictionary_explicit_overrides():
    cols = ["f1", "f2", "label"]
    dd = resolve_data_dictionary(
        {"target_column": "label", "positive_label": 1, "sensitive_feature_columns": ["f1"]},
        cols,
    )
    assert dd.target_column == "label"
    assert dd.target_explicit is True
    assert dd.sensitive_feature_columns == ["f1"]


# ── compliance matrix verdict derivation ─────────────────────────────────────

def _base_state(**over):
    state = {
        "engagement_id": "eng-x", "scope_gate": {},
        "verifier_critiques": {
            "T09_model_card": {"verdict": "accept", "article_citations": ["Art.13", "Art.15"]},
            "T06_datasheet_for_datasets": {"verdict": "accept", "article_citations": ["Art.10"]},
        },
        "phase_artefacts": {
            "T09_model_card": {"uri": "minio://x/T09"},
            "T06_datasheet_for_datasets": {"uri": "minio://x/T06"},
        },
        "blocking_findings": [],
        "insufficient_evidence_articles": [],
        "compliance_matrix": {}, "phase_status": {"T09_model_card": "M", "T06_datasheet_for_datasets": "M"},
        "cgsa_phase5_verdict": "PASS", "cgsa_csp_satisfiable": True,
        "intake_completeness_score": 1.0, "cgsa_payload": None,
    }
    state.update(over)
    return state


def test_material_finding_forces_fail():
    from aaa.agents.tier1.phases.compliance_matrix import node_compliance_matrix
    state = _base_state(blocking_findings=[
        {"finding_id": "F1", "materiality": "material", "eu_ai_act_articles": ["Art.15"],
         "description": "robustness probe failed"},
    ])
    node_compliance_matrix(state)
    assert state["compliance_matrix"]["Art.15"] == "FAIL"
    assert state["final_verdict"] == "FAIL"


def test_insufficient_not_pass():
    from aaa.agents.tier1.phases.compliance_matrix import node_compliance_matrix
    state = _base_state(insufficient_evidence_articles=["Art.15"])
    node_compliance_matrix(state)
    assert state["compliance_matrix"]["Art.15"] == "INSUFFICIENT_EVIDENCE"
    # Core high-risk article unverifiable → disclaimer flagged, never clean PASS.
    assert state["opinion_disclaimer"] is True
    assert state["final_verdict"] == "PASS_WITH_OBSERVATIONS"


def test_admitted_no_findings_pass():
    from aaa.agents.tier1.phases.compliance_matrix import node_compliance_matrix
    state = _base_state()
    node_compliance_matrix(state)
    assert state["compliance_matrix"]["Art.10"] == "PASS"
    assert state["compliance_matrix"]["Art.13"] == "PASS"


# ── auditor opinion ──────────────────────────────────────────────────────────

def test_opinion_disclaimer_when_core_insufficient():
    from aaa.agents.tier2.report_architect import _auditor_opinion
    decl = {
        "compliance_matrix": {"Art.15": "INSUFFICIENT_EVIDENCE"},
        "opinion_disclaimer": True, "material_findings_count": 0,
        "blocking_findings": [], "stage_a": {"system_name": "CreditGuard"},
    }
    op = _auditor_opinion(decl, "PASS_WITH_OBSERVATIONS")
    assert op["opinion_type"] == "disclaimer_of_opinion"
    assert "Art.15" in op["basis_paragraph"]


def test_opinion_adverse_on_fail():
    from aaa.agents.tier2.report_architect import _auditor_opinion
    decl = {"compliance_matrix": {"Art.15": "FAIL"}, "blocking_findings": [],
            "stage_a": {"system_name": "S"}}
    assert _auditor_opinion(decl, "FAIL")["opinion_type"] == "adverse"


def test_opinion_unqualified_clean_pass():
    from aaa.agents.tier2.report_architect import _auditor_opinion
    decl = {"compliance_matrix": {"Art.15": "PASS"}, "material_findings_count": 0,
            "blocking_findings": [], "stage_a": {"system_name": "S"}}
    assert _auditor_opinion(decl, "PASS")["opinion_type"] == "unqualified"


# ── CGSA retrieval failure ≠ governance FAIL ──────────────────────────────────

def test_cgsa_retrieval_failure_marks_insufficient_not_fail(monkeypatch):
    """A CGSA pull/ingest failure is an evidence-availability problem.

    The GovernanceAgent escalation must NOT stamp ``cgsa_phase5_verdict="FAIL"``
    (which the compliance matrix treats as a hard adverse FAIL). It must instead
    mark the governance articles INSUFFICIENT_EVIDENCE so the opinion is a
    disclaimer for them, not a blanket non-conformity.
    """
    from aaa.agents.tier2 import governance_agent as gov
    from aaa.tools.cgsa_pull import CGSAPullError

    def _boom(*_a, **_k):
        raise CGSAPullError("offline_mode_requires_fixture_dir", {"hint": "no fixture"})

    monkeypatch.setattr(gov, "cgsa_pull", _boom)
    agent = gov.GovernanceAgent(EvidenceStore())
    dispatch = {
        "phase_id": "P5",
        "evidence_uris": [],
        "declaration_summary": {"engagement_id": "eng-esc", "cgsa_assessment_id": "cgsa-x"},
    }
    report = asyncio.run(agent.process(dispatch))
    delta = report["declaration_verification_delta"]

    # No spurious FAIL verdict is emitted on a retrieval failure.
    assert "cgsa_phase5_verdict" not in delta
    assert delta.get("cgsa_phase5_verdict") != "FAIL"
    # Governance articles are flagged for the matrix's INSUFFICIENT_EVIDENCE path.
    assert set(delta["insufficient_evidence_articles"]) == {
        "Art.9", "Art.12", "Art.17", "Art.72"
    }
    assert delta["hitl_required"] is True


def test_cgsa_retrieval_failure_yields_disclaimer_not_adverse():
    """End-to-end: the escalation delta routes through the compliance matrix to
    PASS_WITH_OBSERVATIONS + disclaimer, never an adverse FAIL."""
    from aaa.agents.tier1.phases.agent_runner import _apply_delta
    from aaa.agents.tier1.phases.compliance_matrix import node_compliance_matrix

    # cgsa_phase5_verdict stays unset (None) because CGSA was never ingested.
    state = _base_state(cgsa_phase5_verdict=None)
    _apply_delta(state, {
        "hitl_required": True,
        "hitl_reason": "cgsa_pull failed: offline_mode_requires_fixture_dir",
        "insufficient_evidence_articles": ["Art.9", "Art.12", "Art.17", "Art.72"],
        "phase_artefacts": {},
    })
    node_compliance_matrix(state)

    for art in ("Art.9", "Art.12", "Art.17", "Art.72"):
        assert state["compliance_matrix"][art] == "INSUFFICIENT_EVIDENCE"
    assert state["final_verdict"] == "PASS_WITH_OBSERVATIONS"
    assert state["final_verdict"] != "FAIL"
    assert state["opinion_disclaimer"] is True
