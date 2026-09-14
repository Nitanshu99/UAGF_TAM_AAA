"""Evidence written by one store must be readable by another.

This is the guarantee the report renderer depends on and the in-memory backend
cannot give: the pipeline writes figures in one process, ``python -m aaa
report`` resolves them in another. A second ``EvidenceStore`` over the same
bucket stands in for that second process.
"""
from __future__ import annotations

from aaa.platform.evidence import EvidenceStore
from aaa.platform.evidence.backend.memory import MemoryBackend
from aaa.platform.evidence.backend.minio import MinioBackend
from tests.unit.support.fake_minio import FakeMinio

_BUCKET = "aaa-evidence"


def _store(client: FakeMinio) -> EvidenceStore:
    """Build a store bound to *client* over the MinIO backend."""
    return EvidenceStore(backend=MinioBackend(client, _BUCKET))


def test_artefact_resolves_from_a_new_store_instance():
    """A URI written by one store is readable by another — the reported bug."""
    client = FakeMinio()
    uri = _store(client).store_artefact("eng-1", "phase_6", "fig", {"png": "x"}, "Agent")

    assert _store(client).get_artefact(uri) == {"png": "x"}


def test_index_survives_a_new_store_instance():
    """Provenance metadata is readable by a later process too."""
    client = FakeMinio()
    _store(client).store_artefact("eng-1", "phase_6", "T14", {"k": 1}, "Agent")

    index = _store(client).get_index("eng-1")

    assert len(index) == 1
    assert index[0]["created_by_agent"] == "Agent"


def test_index_is_scoped_per_engagement():
    """Entries from another engagement never leak into the index."""
    store = _store(FakeMinio())
    store.store_artefact("eng-1", "phase_6", "T14", {"k": 1}, "Agent")
    store.store_artefact("eng-2", "phase_6", "T14", {"k": 2}, "Agent")

    assert [e["engagement_id"] for e in store.get_index("eng-1")] == ["eng-1"]


def test_memory_backend_does_not_share_state():
    """Contrast: the memory backend is per-instance, which is why figures were lost.

    The backend is constructed rather than inherited from ``EVIDENCE_BACKEND``:
    this test is about ``MemoryBackend``, not about what the environment happens
    to select, and once a real run sets ``minio`` the two are different things.
    """
    uri = EvidenceStore(MemoryBackend()).store_artefact(
        "eng-1", "phase_6", "fig", {"png": "x"}, "Agent")

    assert EvidenceStore(MemoryBackend()).get_artefact(uri) is None
