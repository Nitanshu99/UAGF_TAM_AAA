"""The real case-06 CGSA builds a T14 that validates, with all 36 rows named.

Mariposa-Edu GmbH is a real provider, so their bundle is not distributed and this
test skips wherever it is absent (see ``.gitignore``). Where it is present it is
the strongest check there is: the a4b1ac run's T14 carried 108 schema errors.
"""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

#: The bundle's evaluated export, whatever its id (the bundle is not distributed).
CGSA = next((p for p in sorted(Path("mock/06_mariposa_edu_gmbh/cgsa").glob("*.json"))
             if '"final_maturity_score"' in p.read_text(encoding="utf-8")), Path("absent.json"))
pytestmark = pytest.mark.skipif(not CGSA.is_file(), reason="case-06 bundle not present")


def _built_t14() -> tuple[dict, dict]:
    from aaa.agents.tier2.governance_agent.t14 import build_t14
    from aaa.tools.cgsa_ingest import cgsa_ingest

    payload = json.loads(CGSA.read_text(encoding="utf-8"))
    result = cgsa_ingest(payload, phase1_risk_tier="high", strict=False)
    spawn = {"cyber_spawn": False, "cyber_rationale": "", "privacy_spawn": False,
             "privacy_rationale": ""}
    return payload, build_t14("eng-case06", result, {"risk_tier": "high"}, spawn, False,
                              "2026-09-13T00:00:00+00:00")


def test_the_whole_t14_validates() -> None:
    """Zero errors against the template, not only in the roadmap."""
    _, t14 = _built_t14()
    schema = json.loads(Path("templates/T14_governance_findings.json").read_text(encoding="utf-8"))
    errors = [f"{list(e.path)}: {e.message}"
              for e in jsonschema.Draft202012Validator(schema).iter_errors(t14)]
    assert not errors, errors


def test_all_36_rows_are_named_as_the_cgsa_names_them() -> None:
    """Row 1 is C36, named; no row is blank."""
    payload, t14 = _built_t14()
    rows = t14["remediation_roadmap"]
    assert len(rows) == 36
    assert [r["control_name"] for r in rows] == [
        r["control_name"] for r in payload["remediation_roadmap"]]
    assert rows[0]["control_id"] == "C36"
    assert rows[0]["control_name"] == ("Incident, Failure, Nonconformity, and Corrective "
                                       "Action Management")
