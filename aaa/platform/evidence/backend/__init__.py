"""Storage backends behind :class:`aaa.platform.evidence.EvidenceStore`.

The store issues ``minio://<engagement>/<phase>/<name>`` URIs regardless of
where bytes actually live. A backend answers four questions — put/get a
payload, append/list an index entry — and nothing else, so swapping one for
another cannot change what callers see.

``memory`` is the default: process-local, zero infrastructure, deterministic
for tests. ``minio`` persists across processes, which is what report rendering
needs, since it runs in a different process from the pipeline that produced the
figures.

Both issue the *same* ``minio://`` URIs, which is the seam's whole point and
also finding P9's: a deliverable citing one cannot tell whether the address will
still resolve tomorrow.  ``durable`` is that fact, asked of the backend rather
than re-derived from the environment by each caller that cares.
"""
from __future__ import annotations

from typing import Any, Protocol


class EvidenceBackend(Protocol):
    """Storage operations an evidence backend must provide."""

    #: Whether stored bytes outlive the process that wrote them.  A URI issued
    #: by a backend that says ``False`` is an address inside this process and
    #: nowhere else, however permanent ``minio://`` makes it look.
    durable: bool

    def put_payload(self, uri: str, payload: Any) -> None:
        """Persist *payload* under *uri*."""
        raise NotImplementedError

    def get_payload(self, uri: str) -> Any | None:
        """Return the payload stored under *uri*, or ``None`` if absent."""
        raise NotImplementedError

    def put_index_entry(self, entry: dict) -> None:
        """Append one provenance metadata *entry*."""
        raise NotImplementedError

    def list_index(self, engagement_id: str) -> list[dict]:
        """Return every index entry recorded for *engagement_id*."""
        raise NotImplementedError


def _minio_backend() -> EvidenceBackend:
    """Build the MinIO-backed backend from settings.

    :returns: A backend persisting to the configured bucket.
    :rtype: EvidenceBackend
    :raises RuntimeError: If the client cannot be built or the bucket reached.
    """
    from minio import Minio

    from aaa.platform.evidence.backend.minio import MinioBackend
    from aaa.settings import settings

    try:
        client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        return MinioBackend(client, settings.minio_bucket)
    except Exception as exc:
        raise RuntimeError(
            f"EVIDENCE_BACKEND=minio but MinIO at {settings.minio_endpoint} is "
            f"unusable ({type(exc).__name__}: {exc}). Refusing to fall back to "
            f"in-memory storage — artefacts would be silently unrecoverable."
        ) from exc


def make_backend() -> EvidenceBackend:
    """Build the backend named by ``EVIDENCE_BACKEND``.

    Never degrades a configured ``minio`` backend to ``memory``: a store that
    silently forgets what it was asked to persist is the failure this seam
    exists to prevent.

    :returns: A backend instance; in-memory unless configured otherwise.
    :rtype: EvidenceBackend
    :raises RuntimeError: If MinIO is selected but unusable.
    """
    from aaa.platform.evidence.backend.memory import MemoryBackend
    from aaa.settings import settings

    # str() because pylint infers pydantic's FieldInfo, not the resolved value.
    if str(settings.evidence_backend).strip().lower() == "minio":
        return _minio_backend()
    return MemoryBackend()


__all__ = ["EvidenceBackend", "make_backend"]
