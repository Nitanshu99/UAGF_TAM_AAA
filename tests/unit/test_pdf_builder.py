"""Unit tests for the platypus report builder (rendered from real fixtures)."""
from __future__ import annotations

import json
from pathlib import Path

from aaa.tools.report_render.pdf.builder import build_pdf

_DIR = Path("tests/fixtures/customer_finclear")


def _load(suffix: str) -> dict:
    """Load one finclear deliverable JSON."""
    return json.loads((_DIR / f"eng-01_finclear_gmbh_{suffix}.json").read_text("utf-8"))


def test_full_fixture_renders_multipage_pdf() -> None:
    """The finclear T18+T17+state renders a non-trivial, valid PDF."""
    pdf = build_pdf(_load("T18"), _load("T17"), _load("audit_state"), store=None)
    assert pdf.startswith(b"%PDF")
    assert pdf.count(b"/Type /Page") >= 2  # cover + at least one content page
    assert len(pdf) > 5000


def test_minimal_t18_still_renders() -> None:
    """A bare T18 with no matrix/state renders without raising."""
    pdf = build_pdf({"engagement_id": "eng-min", "final_verdict": "PASS",
                     "executive_summary": "All checks passed."})
    assert pdf.startswith(b"%PDF")


def test_external_evidence_error_renders_gracefully() -> None:
    """An external-provider error stub renders the unavailable notice."""
    state = {"xai_evidence": {"evidence_source": "external", "error": "not_found"},
             "security_evidence": {"evidence_source": "external", "error": "timeout"}}
    pdf = build_pdf({"engagement_id": "eng-err", "final_verdict": "FAIL"},
                    audit_state=state)
    assert pdf.startswith(b"%PDF")
