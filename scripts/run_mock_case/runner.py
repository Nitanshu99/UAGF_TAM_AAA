"""The mock-case pipeline runner."""
from __future__ import annotations

import json
import sys

from scripts.run_mock_case.drive import (
    configure_logging,
    create_engagement,
    dispatch_run,
    submit_intake,
)
from scripts.run_mock_case.env import REPO_ROOT, bootstrap, unbuffer_output
from scripts.run_mock_case.evidence import preflight_evidence_backend
from scripts.run_mock_case.harness import audit_lines, report_harness
from scripts.run_mock_case.summary import print_result
from scripts.run_mock_case.uploads import upload_case_files


def main(case: str) -> int:
    """Run one mock case through the full audit pipeline via the API.

    :param case: Mock case folder name under ``mock/``.
    :returns: Process exit code.
    """
    unbuffer_output()
    case_dir = REPO_ROOT / "mock" / case
    if not case_dir.exists():
        print(f"error: mock case not found: {case_dir}", file=sys.stderr)
        return 2
    bootstrap(case_dir)
    rc = preflight_evidence_backend()
    if rc:
        return rc
    audit_before = len(audit_lines())

    from fastapi.testclient import TestClient

    import aaa.api.store as store_mod
    from aaa.api.main import app
    from aaa.data.writer import normalized_company_name

    configure_logging()
    client = TestClient(app)
    eid = f"eng-{case}"
    stage_a = json.loads((case_dir / "stage_a.json").read_text())
    stage_b = json.loads((case_dir / "stage_b.json").read_text())
    create_engagement(client, eid, stage_a)
    upload_case_files(client, eid, case_dir, stage_b)
    if not submit_intake(client, case, eid, stage_a, stage_b):
        return 1
    if not dispatch_run(client, case, eid):
        return 1
    state = store_mod.FINAL_STATES.get(eid, {})
    print_result(case, state)
    report_harness(audit_lines()[audit_before:])
    company = normalized_company_name(stage_a.get("provider_name"))
    print(f"\nsaved → data/customer/{company}/  (audit_state + T17 + T18)")
    return 0


__all__ = ["main"]
