"""Evidence store issuing MinIO-style URIs over a swappable backend.

URI construction, hashing and provenance metadata live here; where the bytes
actually rest is the backend's business (see
:mod:`aaa.platform.evidence.backend`). Keeping that split means the same URI
written by the pipeline resolves later from the report process, without any of
the 90-odd call sites changing.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Optional

from aaa.platform.evidence.backend import EvidenceBackend, make_backend
from aaa.platform.evidence.contract import contract_fields
from aaa.platform.evidence.file_record import file_record


def _now() -> str:
    """Return the current UTC timestamp in ISO-8601 form."""
    return datetime.now(timezone.utc).isoformat()


class EvidenceStore:
    """Stores audit artefacts and uploaded files, indexed per engagement."""

    def __init__(self, backend: Optional[EvidenceBackend] = None) -> None:
        """Build a store over *backend*.

        :param backend: Storage backend; the configured default when omitted.
        :type backend: EvidenceBackend | None
        """
        self._backend: EvidenceBackend = backend if backend is not None else make_backend()

    @property
    def is_durable(self) -> bool:
        """Whether the URIs this store issues resolve after the process exits.

        A backend that does not claim durability is not assumed to have it: an
        injected double is process-local until it says otherwise, and the
        conservative reading is the one that cannot mislabel a deliverable.

        :returns: ``True`` only when the backend persists what it is given.
        """
        return bool(getattr(self._backend, "durable", False))

    def store_artefact(self, engagement_id: str, phase: str, artefact_type: str,
                       content: Any, agent_name: str) -> str:
        """Store a JSON artefact and return its URI.

        :param engagement_id: Engagement the artefact belongs to.
        :param phase: Pipeline phase key, e.g. ``"phase_5"``.
        :param artefact_type: Template identifier, e.g. ``"T14_governance_findings"``.
        :param content: JSON-serialisable payload.
        :param agent_name: Producing agent (provenance).
        :returns: The MinIO-style artefact URI.
        """
        sha256 = hashlib.sha256(json.dumps(content).encode()).hexdigest()
        uri = f"minio://{engagement_id}/{phase}/{artefact_type}_{sha256[:8]}.json"
        self._backend.put_payload(uri, content)
        self._backend.put_index_entry({
            "engagement_id": engagement_id, "phase": phase,
            "artefact_type": artefact_type, "uri": uri, "sha256": sha256,
            "created_at": _now(), "created_by_agent": agent_name,
            # Checked against its template where every artefact passes (T-20260913-018).
            **contract_fields(artefact_type, content, uri),
        })
        return uri

    def get_artefact(self, uri: str) -> Optional[Any]:
        """Return the artefact stored under *uri*, or ``None``."""
        return self._backend.get_payload(uri)

    def get_index(self, engagement_id: str) -> list[dict]:
        """Return the metadata index entries for *engagement_id*."""
        return self._backend.list_index(engagement_id)

    def store_file(self, engagement_id: str, phase: str, artefact_type: str,
                   filename: str, content_type: str, data: bytes, agent_name: str) -> str:
        """Store binary file bytes once, and return their content-addressed URI.

        The URI carries the content hash, so the same bytes under the same role
        are the same artefact. The wizard stores its uploads on every Streamlit
        rerun, and each call used to append an index entry: one run indexed eight
        intake documents about 120 times (T-20260913-021). A URI whose payload is
        already held with the same hash is returned without writing again. The
        index entry is written before the payload, so an interrupted store can
        leave a duplicate entry on retry, never a payload with no entry.

        :param filename: Original filename (sanitised into the URI).
        :param content_type: MIME type of the upload.
        :param data: Raw file bytes (persisted base64-encoded).
        :returns: The MinIO-style file URI.
        """
        uri, entry, payload = file_record(engagement_id, phase, artefact_type, filename,
                                          content_type, data, agent_name)
        held = self._backend.get_payload(uri)
        if isinstance(held, dict) and held.get("sha256") == payload["sha256"]:
            return uri
        self._backend.put_index_entry(entry)
        self._backend.put_payload(uri, payload)
        return uri
