"""Defects the 2026-09-12 real Mariposa run surfaced, locked in.

Each test names the symptom the run showed; see the cross-validation report of
that run for the numbers.
"""
from __future__ import annotations

from aaa.agents.tier1.phases.compliance_matrix.evidence_entry import _evidence_entry
from aaa.ui.wizard.step4.header import article_rows, article_score
from aaa.ui.wizard.step4.kpis import matrix_counts
from aaa.ui.wizard.step4.status import degraded_reason
from scripts.bootstrap.main import mock_overrides


def _state(t14_verdict: str) -> dict:
    return {
        "phase_artefacts": {"T14_governance_findings": {
            "uri": "minio://aaa-evidence/eng/T14.json", "sha256": "abc",
            "template_id": "T14_governance_findings"}},
        "verifier_critiques": {"T14_governance_findings": {"verdict": t14_verdict}},
        "cgsa_payload": {"eu_ai_act_compliance_matrix": {
            "article_50": {"controls_mapped": ["C22"]}}},
        "compliance_matrix": {"Art.50": "FAIL"},
    }


def test_a_cgsa_backed_verdict_cites_the_governance_artefact() -> None:
    """Art.50 failed on control C22 and T17 carried no evidence URI for it."""
    entry = _evidence_entry(_state("accept"), "Art.50", "FAIL", [])
    assert entry["cgsa_control_ids"] == ["C22"]
    assert "T14_governance_findings" in entry["supporting_template_ids"]
    assert entry["evidence_uris"] == ["minio://aaa-evidence/eng/T14.json"]


def test_a_rejected_governance_artefact_still_admits_nothing() -> None:
    entry = _evidence_entry(_state("escalate_hitl"), "Art.50", "FAIL", [])
    assert "T14_governance_findings" not in entry["supporting_template_ids"]
    assert entry["evidence_uris"] == []


_MATRIX = {"Art.6": "PASS", "Art.10": "FAIL", "Art.10§2(f)": "INSUFFICIENT_EVIDENCE",
           "Art.15": "FAIL", "Art.15§1": "INSUFFICIENT_EVIDENCE", "Annex_III": "PASS"}


def test_the_tiles_count_articles_not_paragraph_rows() -> None:
    """The run showed 4/17 with Art.10 and Art.15 counted twice."""
    assert set(article_rows(_MATRIX)) == {"Art.6", "Art.10", "Art.15", "Annex_III"}
    counts = matrix_counts(_MATRIX)
    assert (counts["total"], counts["met"], counts["unmet"], counts["unknown"]) == (4, 2, 2, 0)
    assert article_score(_MATRIX) == 50.0


def test_the_degraded_banner_names_the_actual_cause() -> None:
    """One lost model call is not 'parts of the assessment did not run'."""
    only_fallback = {"stub_artefact_ids": [], "degraded_phases": [],
                     "fallback_authored_phases": ["P3"], "fallback_critique_ids": []}
    text = degraded_reason(only_fallback)
    assert "model behind them was unavailable" in text
    assert "did not run" not in text
    stubs = {"stub_artefact_ids": ["T03_annex_iii_mapping"], "degraded_phases": ["P1"],
             "fallback_authored_phases": [], "fallback_critique_ids": []}
    assert degraded_reason(stubs).startswith("Parts of the assessment did not run")
    unverified = {"stub_artefact_ids": [], "degraded_phases": [],
                  "fallback_authored_phases": [], "fallback_critique_ids": ["T17_compliance_matrix"]}
    assert "not independently verified" in degraded_reason(unverified)


def test_mock_runs_keep_their_metrics_out_of_the_real_dashboards() -> None:
    """Eight refused mock calls sat in the real run's error ratio."""
    env = mock_overrides({}, "http://127.0.0.1:8765/api/v1")
    assert env["PROMETHEUS_MULTIPROC_DIR"].endswith("logs/metrics-mock")
    assert env["OPENROUTER_API_BASE"] == "http://127.0.0.1:8765/api/v1"
    assert env["OPENROUTER_API_KEY"].startswith("sk-or-v1-mock")
