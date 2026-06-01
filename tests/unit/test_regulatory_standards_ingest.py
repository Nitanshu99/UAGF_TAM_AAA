"""Regression tests for standards PDF ingestion into regulatory_corpus."""
from __future__ import annotations

from pathlib import Path

from scripts import ingest_regulatory_corpus as ingest


def test_standards_pdfs_produce_traceable_chunks():
    checker = ingest.CheckerLookup({}, {}, [])
    for file_name, regulation in (
        ("isae_3000.pdf", "ISAE 3000"),
        ("iso_19011.pdf", "ISO 19011"),
    ):
        path = Path("data/regulatory_corpus") / file_name
        assert path.exists(), f"missing {path}"
        units = ingest.load_units_for_path(path, regulation)
        assert units, f"no structural units parsed for {path}"
        assert all(unit.ref for unit in units[:10])

        chunks = ingest.chunk_units(units, checker)
        assert chunks, f"no chunks produced for {path}"
        for chunk in chunks[:5]:
            assert chunk.payload["regulation"] == regulation
            assert chunk.payload["ref"]
            assert chunk.payload["source_file"] == file_name