"""MinIO-backed evidence storage — survives the process that wrote it.

Object keys are the URI path: ``minio://<engagement>/<phase>/<name>`` becomes
``<engagement>/<phase>/<name>`` inside ``MINIO_BUCKET``. URIs already embedded
in stored T17/T18 payloads therefore keep resolving unchanged.

Payloads are serialised as JSON because both shapes the store writes are
JSON-safe — artefacts by contract, uploaded files as a base64 envelope — so
``get_payload`` hands back exactly the object ``put_payload`` was given.

Index entries are written as one object each under ``<engagement>/_index/``
rather than appended to a shared file: agents run concurrently, and a
read-modify-write of a single index would lose entries.
"""
from __future__ import annotations

import hashlib
import io
import json
from typing import Any

_INDEX_PREFIX = "_index"


class MinioBackend:
    """Evidence backend persisting payloads and index entries to MinIO."""

    #: Objects outlive the process, so a URI written into a delivered T17/T18
    #: still resolves from `aaa report` and from a reviewer's own session.
    durable = True

    def __init__(self, client: Any, bucket: str) -> None:
        """Bind to *client* and ensure *bucket* exists.

        :param client: A ``minio.Minio`` instance (injected for testability).
        :type client: Any
        :param bucket: Target bucket name.
        :type bucket: str
        """
        self._client = client
        self._bucket = bucket
        if not self._client.bucket_exists(bucket):
            self._client.make_bucket(bucket)

    @staticmethod
    def _key(uri: str) -> str:
        """Return the object key for a ``minio://`` *uri*.

        :param uri: MinIO-style artefact URI.
        :type uri: str
        :returns: Object key relative to the bucket.
        :rtype: str
        """
        return uri[len("minio://"):] if uri.startswith("minio://") else uri

    def _put_json(self, key: str, payload: Any) -> None:
        """Write *payload* as a JSON object at *key*."""
        body = json.dumps(payload).encode("utf-8")
        self._client.put_object(
            self._bucket, key, io.BytesIO(body), len(body),
            content_type="application/json",
        )

    def put_payload(self, uri: str, payload: Any) -> None:
        """Persist *payload* under *uri*.

        :param uri: MinIO-style artefact URI.
        :type uri: str
        :param payload: JSON-serialisable content or file envelope.
        :type payload: Any
        """
        self._put_json(self._key(uri), payload)

    def get_payload(self, uri: str) -> Any | None:
        """Return the payload stored under *uri*, or ``None`` when absent.

        A missing key is a miss, not an error — callers treat ``None`` as
        "not in this store" and fall back to other resolution paths.

        :param uri: MinIO-style artefact URI.
        :type uri: str
        :returns: Stored payload, or ``None``.
        :rtype: Any | None
        """
        response = None
        try:
            response = self._client.get_object(self._bucket, self._key(uri))
            return json.loads(response.read().decode("utf-8"))
        except Exception:  # noqa: BLE001 — any miss/decode failure is "absent"
            return None
        finally:
            if response is not None:
                response.close()
                response.release_conn()

    def put_index_entry(self, entry: dict) -> None:
        """Append one provenance metadata *entry* as its own object.

        :param entry: Index record carrying at least ``engagement_id``.
        :type entry: dict
        """
        engagement_id = str(entry.get("engagement_id", "unknown"))
        digest = hashlib.sha256(json.dumps(entry, sort_keys=True).encode()).hexdigest()
        self._put_json(f"{engagement_id}/{_INDEX_PREFIX}/{digest[:16]}.json", entry)

    def list_index(self, engagement_id: str) -> list[dict]:
        """Return every index entry recorded for *engagement_id*.

        :param engagement_id: Engagement to filter by.
        :type engagement_id: str
        :returns: Index entries, ordered by creation timestamp.
        :rtype: list[dict]
        """
        prefix = f"{engagement_id}/{_INDEX_PREFIX}/"
        entries: list[dict] = []
        for obj in self._client.list_objects(self._bucket, prefix=prefix, recursive=True):
            payload = self.get_payload(obj.object_name)
            if isinstance(payload, dict):
                entries.append(payload)
        return sorted(entries, key=lambda e: str(e.get("created_at", "")))
