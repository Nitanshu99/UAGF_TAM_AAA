"""A CLI run must put the customer's documents in front of the audit.

``stage_b.json`` in a mock bundle names its supporting documents as filesystem
paths. ``client_doc_ingest`` resolves ``minio://`` URIs and nothing else, so
those paths loaded as ``None``: seven warnings, zero chunks indexed, and every
phase's retrieval answering "Client-doc seed: 0 passage(s)". The audit then
reported on a dossier it had never opened, and nothing in the result said so —
the 2026-09-11 Mariposa CLI run scored 93.3% coverage with 5 article FAILs
against the UI run's 100% and 11, on identical inputs.
"""
from __future__ import annotations

import argparse
import json
import pathlib

import pytest

from aaa.agents.intake_validator.errors import _CLIENT_DOC_URI_FIELDS
from aaa.cli.seed.documents import _resolve, seed_client_documents
from aaa.platform.evidence import EvidenceStore


@pytest.fixture(name="bundle")
def _bundle(tmp_path: pathlib.Path) -> pathlib.Path:
    """A minimal intake bundle with one real document on disk."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "risk_management_system.txt").write_text("Risk management file.", encoding="utf-8")
    (tmp_path / "stage_a.json").write_text("{}", encoding="utf-8")
    return tmp_path


def _stage_b(bundle: pathlib.Path) -> dict:
    return {"risk_management_file_uri": f"{bundle.name}/docs/risk_management_system.txt"}


def test_a_declared_document_becomes_a_stored_artefact(bundle: pathlib.Path) -> None:
    """The path is replaced by a URI the ingest can actually open."""
    store = EvidenceStore()
    stage_b = _stage_b(bundle)
    unresolved = seed_client_documents(store, "eng-t", stage_b, bundle)

    assert unresolved == []
    uri = stage_b["risk_management_file_uri"]
    assert uri.startswith("minio://eng-t/customer_uploads/")
    assert "risk_management_file_uri" in uri  # keyed by the field, as the UI does


def test_the_stored_bytes_are_the_document(bundle: pathlib.Path) -> None:
    """Staging must carry the content, not just mint a URI."""
    from aaa.tools.client_doc_ingest.loading import _load_document

    store = EvidenceStore()
    stage_b = _stage_b(bundle)
    seed_client_documents(store, "eng-t", stage_b, bundle)
    assert _load_document(stage_b["risk_management_file_uri"], store) == b"Risk management file."


def test_a_missing_document_is_reported_not_swallowed(bundle: pathlib.Path) -> None:
    """Silence here is what let an audit report on an unopened dossier."""
    store = EvidenceStore()
    stage_b = {"risk_management_file_uri": "docs/does_not_exist.txt"}
    assert seed_client_documents(store, "eng-t", stage_b, bundle) == ["risk_management_file_uri"]
    # Left as-is rather than rewritten to a URI that resolves to nothing.
    assert stage_b["risk_management_file_uri"] == "docs/does_not_exist.txt"


def test_an_already_stored_uri_is_left_alone(bundle: pathlib.Path) -> None:
    """The UI path already stores its uploads; re-staging would duplicate them."""
    store = EvidenceStore()
    original = "minio://eng-t/customer_uploads/risk_management_file_uri_abc_f.txt"
    stage_b = {"risk_management_file_uri": original}
    assert seed_client_documents(store, "eng-t", stage_b, bundle) == []
    assert stage_b["risk_management_file_uri"] == original


def test_resolution_does_not_depend_on_the_working_directory(bundle: pathlib.Path) -> None:
    """`make m6-case4` and a bare `python -m aaa.cli run` must behave the same."""
    assert _resolve("docs/risk_management_system.txt", bundle) is not None
    assert _resolve("somewhere/else/docs/risk_management_system.txt", bundle) is not None
    assert _resolve(str(bundle / "docs" / "risk_management_system.txt"), bundle) is not None
    assert _resolve("docs/nope.txt", bundle) is None


def test_every_client_doc_field_is_covered(bundle: pathlib.Path) -> None:
    """The seeder must cover exactly the fields the ingest reads."""
    store = EvidenceStore()
    for field in _CLIENT_DOC_URI_FIELDS:
        (bundle / "docs" / f"{field}.txt").write_text(field, encoding="utf-8")
    stage_b = {f: f"docs/{f}.txt" for f in _CLIENT_DOC_URI_FIELDS}
    assert seed_client_documents(store, "eng-t", stage_b, bundle) == []
    assert all(stage_b[f].startswith("minio://") for f in _CLIENT_DOC_URI_FIELDS)


def test_the_cli_seeder_runs_document_staging(bundle: pathlib.Path) -> None:
    """Wired into `_seed_intake`, not merely available to it."""
    (bundle / "stage_b.json").write_text(json.dumps(_stage_b(bundle)), encoding="utf-8")
    store = EvidenceStore()
    from aaa.cli.seed.intake import _seed_intake

    dispatch = _seed_intake(
        store, bundle,
        argparse.Namespace(engagement_id="eng-t", annex_iv_schema_version="1.0.0"))
    stored = store.get_artefact(dispatch["stage_b_uri"])
    assert stored["risk_management_file_uri"].startswith("minio://")
