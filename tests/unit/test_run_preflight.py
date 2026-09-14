"""A run that is not comparable with its baseline must be caught before dispatch.

On 2026-09-11 a paid Mariposa run was dispatched against a self-assessment CGSA
export where the baseline had used the evaluated S5 one. Six article verdicts
softened and nothing logged a word. Both facts needed to stop it were already on
disk: the case document's header ("the real S5 export ... not the mock fixture")
and the export itself, inside the baseline run's own AuditState.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aaa.tools.cgsa_pull.compat import is_evaluated, payload_profile
from aaa.tools.run_preflight.archived import baseline_from_index, find_archived_run
from aaa.tools.run_preflight.header import BaselineError, parse_header

CASE_06 = Path("local/assessments/run_2026-09-10/case_06_mariposa_edu_gmbh.md")
ARCHIVE = Path("data/customer/mariposa_edu_gmbh/runs")


def _control(**over) -> dict:
    """One CGSA control record."""
    base = {"control_id": "C02", "control_name": "x", "maturity_score": 2}
    base.update(over)
    return base


def _payload(controls: list[dict], schema: str, articles: int = 3) -> dict:
    """A CGSA payload wrapping *controls*."""
    return {"schema_version": schema, "domains": [{"controls": controls}],
            "eu_ai_act_compliance_matrix": {f"article_{i}": {} for i in range(articles)}}


def test_a_self_assessment_export_is_not_evaluated() -> None:
    """No threshold means no control can ever produce a non-conformity."""
    payload = _payload([_control(), _control(control_id="C27")], "1.0.0")
    assert is_evaluated(payload) is False
    assert payload_profile(payload)["evaluated_controls"] == 0


def test_an_s5_export_is_evaluated() -> None:
    """Both fields on every control is what the threshold rule needs."""
    payload = _payload(
        [_control(final_maturity_score=1, threshold_score=3),
         _control(control_id="C27", final_maturity_score=2, threshold_score=3)],
        "s5-aaa-adapter-v1.0")
    assert is_evaluated(payload) is True


def test_a_partly_evaluated_export_is_not_treated_as_evaluated() -> None:
    """One control missing its threshold silently drops one article's finding."""
    payload = _payload(
        [_control(final_maturity_score=1, threshold_score=3), _control(control_id="C27")],
        "s5-aaa-adapter-v1.0")
    assert is_evaluated(payload) is False


def test_profile_describes_what_the_matrix_covers() -> None:
    """Article count is the other half of the divergence, not just the fields."""
    assert payload_profile(_payload([_control()], "1.0.0", articles=7))[
        "matrix_articles"] == 7


@pytest.mark.skipif(not CASE_06.is_file(), reason="case document not present")
def test_the_case_document_header_is_machine_readable() -> None:
    """The model pin and CGSA note are stated in the header, not buried."""
    header = parse_header(CASE_06)
    assert header["run_id"].startswith("879efe44")
    assert header["model"] == "openrouter/minimax/minimax-m3"
    assert header["provider_pin"] == "coreweave/fp4"
    assert "not the mock fixture" in (header["cgsa_note"] or "")


# Needs both: the archive names the baseline, and the case document is what it
# has to differ from. The case bundle is gitignored client material, so a clone
# has neither and this skips rather than fails.
@pytest.mark.skipif(not (ARCHIVE / "INDEX.md").is_file() or not CASE_06.is_file(),
                    reason="run archive or case document not present")
def test_the_baseline_is_the_controlled_comparison_not_the_assessed_run() -> None:
    """The document's own run is the pre-fix subject; the archive names the baseline.

    Getting this backwards measures the fix series instead of the new run —
    case 06's archive spans 46.7 % to 100 % coverage under one engagement id.
    """
    assert baseline_from_index(ARCHIVE / "INDEX.md") == "5bfb82de"
    assert baseline_from_index(ARCHIVE / "INDEX.md") != parse_header(CASE_06)["run_id"]


@pytest.mark.skipif(not (ARCHIVE / "INDEX.md").is_file(), reason="archive not present")
def test_the_baseline_run_is_in_the_archive_and_used_an_evaluated_cgsa() -> None:
    """What the baseline audited against, read from the baseline itself."""
    run_dir = find_archived_run("5bfb82de")
    state = json.loads(next(run_dir.glob("*_audit_state.json")).read_text("utf-8"))
    assert is_evaluated(state["cgsa_payload"]) is True
    assert state["regulatory_coverage_pct"] == 100.0


def test_a_missing_case_document_is_explained_not_a_traceback(tmp_path: Path) -> None:
    """A clone has no case document for a real-client case, and that is fine.

    The README promises a clear error here; without this the parser raised a
    bare FileNotFoundError from inside `open`.
    """
    with pytest.raises(BaselineError, match="is not present"):
        parse_header(tmp_path / "no-such-case.md")


def test_an_unknown_run_names_the_archive_it_searched(tmp_path: Path) -> None:
    """A missing baseline is an error, never a silently skipped check."""
    with pytest.raises(BaselineError, match="not in the run archive"):
        find_archived_run("deadbeef", root=str(tmp_path))


@pytest.mark.skipif(not Path("mock/06_mariposa_edu_gmbh/cgsa").is_dir(),
                    reason="mock bundle not present")
def test_case_06_ships_the_evaluated_export_the_baseline_used() -> None:
    """The fixture directory must be able to reproduce the baseline.

    Regression guard for the 2026-09-11 run: every shipped fixture was the thin
    ``1.0.0`` dialect, so no fixture-backed run of case 06 could reproduce the
    baseline's verdicts on Arts. 5, 11, 12, 14, 50 or 72.
    """
    evaluated = [p for p in Path("mock/06_mariposa_edu_gmbh/cgsa").glob("*.json")
                 if is_evaluated(json.loads(p.read_text("utf-8")))]
    assert evaluated, "case 06 ships no evaluated CGSA export"


@pytest.mark.skipif(not Path("mock/06_mariposa_edu_gmbh/cgsa").is_dir(),
                    reason="mock bundle not present")
def test_the_evaluated_export_wins_over_the_self_assessment() -> None:
    """Both exist for Mariposa; resolution must not call that a tie and give up."""
    from aaa.tools.cgsa_pull import resolve_assessment_id
    from aaa.tools.cgsa_pull.discover import discover_assessments

    resolved = resolve_assessment_id("Mariposa-Edu GmbH", "Mariposa", ["mock"])
    evaluated = {a["assessment_id"] for a in discover_assessments(["mock"]) if a["evaluated"]}
    assert resolved in evaluated
