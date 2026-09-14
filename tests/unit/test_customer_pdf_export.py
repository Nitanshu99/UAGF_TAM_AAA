"""Unit tests for the per-company PDF written by save_customer_artefacts."""
from __future__ import annotations

import json
from pathlib import Path

from aaa.data.writer import save_customer_artefacts

_DIR = Path("tests/fixtures/customer_finclear")


class _FakeStore:
    """Resolves the T17/T18 artefact URIs to the persisted fixture payloads."""

    def get_artefact(self, uri: str | None) -> dict | None:
        """Return the fixture payload matching the artefact type in *uri*."""
        if not uri:
            return None
        for marker, suffix in (("T17", "T17"), ("T18", "T18")):
            if marker in uri:
                return json.loads(
                    (_DIR / f"eng-01_finclear_gmbh_{suffix}.json").read_text("utf-8"))
        return None


def test_finish_writes_pdf_next_to_jsons(tmp_path, monkeypatch) -> None:
    """A completed run leaves <eid>_audit_report.pdf in the company folder."""
    monkeypatch.setenv("AAA_DATA_DIR", str(tmp_path))
    state = json.loads((_DIR / "eng-01_finclear_gmbh_audit_state.json").read_text("utf-8"))
    cdir = save_customer_artefacts("eng-01_finclear_gmbh", state, _FakeStore())
    assert cdir is not None
    pdf_path = cdir / "eng-01_finclear_gmbh_audit_report.pdf"
    assert pdf_path.exists()
    assert pdf_path.read_bytes().startswith(b"%PDF")
    assert (cdir / "eng-01_finclear_gmbh_audit_state.json").exists()
