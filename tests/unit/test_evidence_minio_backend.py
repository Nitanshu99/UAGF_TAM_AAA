"""Storage semantics of the MinIO evidence backend."""
from __future__ import annotations

import base64

from aaa.platform.evidence import EvidenceStore
from aaa.platform.evidence.backend.minio import MinioBackend
from tests.unit.support.fake_minio import FakeMinio

_BUCKET = "aaa-evidence"


def _store(client: FakeMinio) -> EvidenceStore:
    """Build a store bound to *client* over the MinIO backend."""
    return EvidenceStore(backend=MinioBackend(client, _BUCKET))


def test_bucket_created_when_absent():
    """The backend provisions its bucket rather than assuming one."""
    client = FakeMinio()
    MinioBackend(client, _BUCKET)
    assert _BUCKET in client.buckets


def test_artefact_round_trips():
    """An artefact comes back exactly as it was stored."""
    store = _store(FakeMinio())
    uri = store.store_artefact("eng-1", "phase_6", "T14", {"verdict": "PASS"}, "Agent")
    assert store.get_artefact(uri) == {"verdict": "PASS"}


def test_object_key_drops_the_scheme():
    """minio://a/b/c is stored under the key a/b/c inside the bucket."""
    client = FakeMinio()
    uri = _store(client).store_artefact("eng-1", "phase_6", "T14", {"k": 1}, "Agent")
    assert (_BUCKET, uri[len("minio://"):]) in client.objects


def test_file_round_trips_binary_payload():
    """Uploaded bytes survive the base64 envelope."""
    store = _store(FakeMinio())
    uri = store.store_file("eng-1", "phase_6", "up", "a.png", "image/png", b"\x89PNG", "Agent")
    payload = store.get_artefact(uri)
    assert payload is not None
    assert base64.b64decode(payload["body_base64"]) == b"\x89PNG"


def test_missing_uri_is_a_miss_not_an_error():
    """An absent key returns None so callers can fall back."""
    assert _store(FakeMinio()).get_artefact("minio://eng-1/phase_6/absent.json") is None


def test_responses_are_closed_and_released():
    """Every get_object response is closed and its connection released."""
    client = FakeMinio()
    store = _store(client)
    store.get_artefact(store.store_artefact("eng-1", "p6", "T14", {"k": 1}, "Agent"))
    assert client.responses and all(r.closed and r.released for r in client.responses)
