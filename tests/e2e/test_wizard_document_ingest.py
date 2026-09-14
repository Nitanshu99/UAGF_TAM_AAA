"""The wizard's upload step, against real Qdrant and real embeddings.

Marked ``e2e`` because it needs the Docker Compose stack and an embedding key.
It exists because the unit tests can only prove the wizard *calls* the ingest;
this proves the call still produces the collection the audit retrieves against
now that ``DocIntelligenceAgent`` is no longer on the wizard's path.

Run with::

    .venv/bin/python -m pytest tests/e2e/test_wizard_document_ingest.py -m e2e
"""
from __future__ import annotations

import pathlib

import pytest

from aaa.platform.evidence import EvidenceStore
from aaa.tools.client_doc_ingest.config import _collection_name, _embeddings_available
from aaa.tools.client_doc_ingest.freshness import reset_tracking
from aaa.tools.client_doc_ingest.search import client_doc_search
from aaa.ui.wizard.pipeline import ingest_documents

pytestmark = pytest.mark.e2e

_DOCS = pathlib.Path("mock/06_mariposa_edu_gmbh/docs")
_FILES = ("mariposa_technical_documentation.txt", "model_card.md",
          "post_market_monitoring_plan.txt")


def _qdrant_up() -> bool:
    """Whether a Qdrant this test can write to is reachable."""
    try:
        from aaa.tools.client_doc_ingest.qdrant import _qdrant_client
        _qdrant_client().get_collections()
        return True
    except Exception:  # noqa: BLE001 — absence is a skip, not a failure
        return False


requires_stack = pytest.mark.skipif(
    not (_embeddings_available() and _qdrant_up() and _DOCS.is_dir()),
    reason="needs Qdrant, an embeddings key, and the mock document bundle")


@pytest.fixture(name="indexed")
def _indexed():
    """Upload three real client documents the way step 1 does."""
    engagement_id = "eng-e2e-wizard-ingest"
    store = EvidenceStore()
    uris = [
        store.store_artefact(engagement_id, "customer_uploads", name,
                             {"filename": name,
                              "content": (_DOCS / name).read_text(encoding="utf-8")},
                             "streamlit")
        for name in _FILES
    ]
    reset_tracking()
    return engagement_id, ingest_documents(engagement_id, uris, store)


@requires_stack
def test_uploads_reach_the_engagement_collection(indexed) -> None:
    """Every uploaded document is indexed, into the collection intake expects."""
    engagement_id, result = indexed
    assert result["error"] is None
    assert result["chunks_indexed"] > 0
    assert len(result["sources"]) == len(_FILES)
    assert result["collection_name"] == _collection_name(engagement_id)


@requires_stack
def test_the_audit_can_retrieve_what_the_customer_uploaded(indexed) -> None:
    """The point of indexing: a phase's query finds the right document.

    This is the assertion that would have caught removing the ingest along with
    the extraction — the form would still work and the audit would quietly lose
    every document the customer supplied at step 1.
    """
    engagement_id, _ = indexed
    hits = client_doc_search(engagement_id, "post-market monitoring plan", top_k=3)
    assert hits
    assert any("post_market_monitoring_plan" in str(hit) for hit in hits)
