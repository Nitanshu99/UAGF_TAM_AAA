"""Evidence-chain accumulation and rerun-safe finding de-duplication."""
from __future__ import annotations

from aaa.agents.tier1.phases.agent_runner import _apply_delta, _evidence_uris
from aaa.tools.findings import make_finding


def test_evidence_uris_accumulates_all_artefacts_intake_first():
    state = {
        "phase_artefacts": {
            "T06_datasheet_for_datasets": {"uri": "minio://p2/T06.json"},
            "T01a_stage_a_triage": {"uri": "minio://a/T01a.json"},
            "T01b_annex_iv_dossier": {"uri": "minio://b/T01b.json"},
            "T02_system_card": {"uri": "minio://p1/T02.json"},
        }
    }
    uris = _evidence_uris(state)
    # Intake leads, every artefact present, de-duplicated.
    assert uris[:2] == ["minio://a/T01a.json", "minio://b/T01b.json"]
    assert "minio://p1/T02.json" in uris and "minio://p2/T06.json" in uris
    assert len(uris) == len(set(uris)) == 4


def test_apply_delta_dedups_findings_on_rerun():
    state = {"phase_artefacts": {}, "blocking_findings": []}
    f = make_finding(
        finding_id="P5-CGSA-COUNT", description="38 vs 10",
        materiality="possibly_material", articles=["Art.17"], source_phase="P5",
    )
    delta = {"blocking_findings": [f]}
    # Same phase re-dispatched twice (two reruns) → still one finding, not three.
    _apply_delta(state, delta)
    _apply_delta(state, delta)
    _apply_delta(state, delta)
    assert len(state["blocking_findings"]) == 1


def test_apply_delta_keeps_distinct_descriptions():
    state = {"phase_artefacts": {}, "blocking_findings": []}
    findings = [
        make_finding(finding_id="P3-DATADICT", description=d,
                     materiality="possibly_material", articles=["Art.11"],
                     source_phase="P3")
        for d in ("no target_column", "no positive_label", "no sensitive_features")
    ]
    _apply_delta(state, {"blocking_findings": findings})
    _apply_delta(state, {"blocking_findings": findings})  # rerun
    assert len(state["blocking_findings"]) == 3  # distinct descriptions preserved
