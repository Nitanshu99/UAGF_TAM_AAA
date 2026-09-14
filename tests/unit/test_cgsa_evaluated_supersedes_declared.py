"""T-20260914-062: every entry point audits against the evaluated CGSA export when one supersedes.

Case 06's wizard found the evaluated export by name while the CLI pulled the declared
self-assessment, and six articles differed between the two runs. Synthetic assessments
stand in for the provider's here.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aaa.agents.tier2.governance_agent.acquire import pull_assessment, source_note
from aaa.tools.cgsa_pull.supersede import evaluated_counterpart


def _assessment(aid: str, org: str, system: str, evaluated: bool) -> dict:
    """A payload carrying just what discovery and the dialect test read."""
    control = {"control_id": "C01", "maturity_score": 2}
    if evaluated:
        control.update(final_maturity_score=2, threshold_score=3)
    return {"schema_version": "s5-aaa-adapter-v1.0" if evaluated else "1.0.0",
            "metadata": {"assessment_id": aid, "organisation_name": org,
                         "system_under_audit": system},
            "domains": [{"domain_id": "D1", "controls": [control]}]}


def _write(root: Path, *payloads: dict) -> str:
    """File each payload as ``<root>/<case>/cgsa/<id>.json``; returns the root."""
    folder = root / "case" / "cgsa"
    folder.mkdir(parents=True, exist_ok=True)
    for payload in payloads:
        (folder / f"{payload['metadata']['assessment_id']}.json").write_text(json.dumps(payload))
    return str(root)


_SELF = _assessment("acme-self-001", "Acme GmbH", "Acme v2.0.0", evaluated=False)
_EVAL = _assessment("acme-eval-9f", "Acme", "Acme scoring platform", evaluated=True)


def test_a_declared_self_assessment_is_superseded_by_its_evaluated_export(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Legal form and version are ignored; the nested system name matches."""
    monkeypatch.setenv("AAA_CGSA_FIXTURE_DIR", _write(tmp_path, _SELF, _EVAL))
    payload, source = pull_assessment("acme-self-001")
    assert payload["metadata"]["assessment_id"] == "acme-eval-9f"
    assert source == {"assessment_id": "acme-eval-9f", "declared_assessment_id": "acme-self-001",
                      "evaluated": True, "superseded": True}
    assert "'acme-self-001', a self-assessment export" in source_note(source)


def test_an_evaluated_declaration_is_read_as_declared(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Nothing supersedes an evaluated export, and no sentence is written."""
    monkeypatch.setenv("AAA_CGSA_FIXTURE_DIR", _write(tmp_path, _SELF, _EVAL))
    payload, source = pull_assessment("acme-eval-9f")
    assert payload["metadata"]["assessment_id"] == "acme-eval-9f"
    assert source["superseded"] is False and source["evaluated"] is True
    assert source_note(source) == ""


def test_no_counterpart_keeps_the_self_assessment_and_says_so(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Cases 01-05 ship only a self-assessment; the state records that it is one."""
    monkeypatch.setenv("AAA_CGSA_FIXTURE_DIR", _write(tmp_path, _SELF))
    _, source = pull_assessment("acme-self-001")
    assert source == {"assessment_id": "acme-self-001", "declared_assessment_id": "acme-self-001",
                      "evaluated": False, "superseded": False}


def test_other_systems_and_ambiguous_matches_supersede_nothing(tmp_path: Path) -> None:
    """A different organisation or system, or two evaluated exports, is no counterpart."""
    other_org = _assessment("beta-eval", "Beta AG", "Acme scoring platform", evaluated=True)
    other_system = _assessment("acme-hr-eval", "Acme GmbH", "Recruiting bot", evaluated=True)
    root = _write(tmp_path, _SELF, other_org, other_system)
    assert evaluated_counterpart(_SELF, [root]) is None
    twin = _assessment("acme-eval-2", "Acme GmbH", "Acme scoring platform v3", evaluated=True)
    assert evaluated_counterpart(_SELF, [_write(tmp_path, _EVAL, twin)]) is None
    assert evaluated_counterpart(_EVAL, [root]) is None
