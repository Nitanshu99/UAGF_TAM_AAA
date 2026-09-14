"""Artefacts record what was declared or measured, and nothing invented in between.

T08 named lawful bases nobody declared (T-20260913-036); T04/T03 recorded a declared
Art. 6(3) derogation as unclaimed (-037).
"""
from __future__ import annotations

from aaa.agents.tier2.data_auditor.t08 import build_t08
from aaa.agents.tier2.scope_agent.derogation import stamp_declared_derogation
from aaa.agents.tier2.scope_agent.t04 import build_t04
from aaa.agents.tier3.privacy_agent.t08_update import update_t08


def _errors(tid: str, payload: dict) -> list[str]:
    """Template violations of *payload*, via the store-time contract check."""
    from aaa.platform.evidence.contract import artefact_schema_errors

    return artefact_schema_errors(tid, payload) or []


def test_a_detected_category_gets_no_invented_basis() -> None:
    """Phase 2: not_declared, no asserted purpose, consultation or DPIA status."""
    t08 = build_t08("eng-t", True, {"special_categories_found": ["health_data"]}, True, "now")
    entry = t08["lawful_basis_entries"][0]
    assert entry["lawful_basis"] == "not_declared"
    assert entry["dpia_conducted"] is None and entry["dpa_consultation_required"] is None
    assert t08["art10_5_statistical_correction_applies"] is None
    assert not _errors("T08_special_category_data_log", t08)


def test_the_privacy_spawn_invents_none_either() -> None:
    """Tier 3: no 'Client declared general public interest', no dpia_conducted False."""
    t08, _cats = update_t08({"special_category_data_present": False}, "eng-t",
                            {"special_category_data_detected": True,
                             "special_categories_found": ["health_data"]})
    entry = t08["lawful_basis_entries"][0]
    assert entry["lawful_basis"] == "not_declared" and entry["dpia_conducted"] is None
    assert "public interest" not in entry["basis_reference"]


def test_a_declared_derogation_is_recorded_not_overwritten() -> None:
    """T04 and each declared T03 entry carry the claim; acceptance is not decided here."""
    stage_a = {"art6_derogation_claimed": True,
               "art6_derogation_rationale": "Narrow procedural task (Art. 6(3)(a))."}
    t04 = build_t04("eng-t", "high", "high", False, ["4"], "now", stage_a)
    assert t04["art6_derogation_claimed"] is True and t04["art6_derogation_accepted"] is None
    assert t04["art6_derogation_rationale"].startswith("Narrow procedural task")
    entries = [{"provenance": "client_declared"}, {"provenance": "phase1_verified"}]
    stamp_declared_derogation(entries, stage_a)
    assert entries[0]["derogation_claimed"] is True and "derogation_claimed" not in entries[1]


def test_an_unmeasured_task_names_no_primary_metric() -> None:
    """No evaluation ran, so no metric was chosen for it."""
    from aaa.tools.metric_suite import metric_suite

    for task in ("ranking", "classification", "regression"):
        assert metric_suite(y_true=None, y_pred=None, y_proba=None,
                            task=task)["primary_metric"] == "not measured"


def test_t18_does_not_invent_a_version() -> None:
    from aaa.agents.tier2.report_architect.t18.sections import metadata_section

    assert metadata_section({}, {})["version"] == "not declared"
    assert metadata_section({}, {"version": "1.0.0"})["version"] == "1.0.0"
