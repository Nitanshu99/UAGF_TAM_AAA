"""Process-local evidence backend — the historic EvidenceStore behaviour.

Holds payloads and index entries in plain dicts. Nothing survives the process,
which is correct for tests and for any single-process run, and is exactly why
report rendering needs a persistent backend instead.
"""
from __future__ import annotations

from typing import Any


class MemoryBackend:
    """In-memory payload and index storage."""

    #: Nothing here survives the interpreter, so nothing it addresses does.
    durable = False

    def __init__(self) -> None:
        self._objects: dict[str, Any] = {}
        self._index: list[dict] = []

    def put_payload(self, uri: str, payload: Any) -> None:
        """Persist *payload* under *uri*.

        :param uri: MinIO-style artefact URI.
        :type uri: str
        :param payload: JSON-serialisable content or file envelope.
        :type payload: Any
        """
        self._objects[uri] = payload

    def get_payload(self, uri: str) -> Any | None:
        """Return the payload stored under *uri*, or ``None``.

        :param uri: MinIO-style artefact URI.
        :type uri: str
        :returns: Stored payload, or ``None`` when absent.
        :rtype: Any | None
        """
        return self._objects.get(uri)

    def put_index_entry(self, entry: dict) -> None:
        """Append one provenance metadata *entry*.

        :param entry: Index record carrying at least ``engagement_id``.
        :type entry: dict
        """
        self._index.append(entry)

    def list_index(self, engagement_id: str) -> list[dict]:
        """Return every index entry recorded for *engagement_id*.

        :param engagement_id: Engagement to filter by.
        :type engagement_id: str
        :returns: Matching index entries in insertion order.
        :rtype: list[dict]
        """
        return [e for e in self._index if e.get("engagement_id") == engagement_id]
