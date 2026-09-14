"""URI → raw-bytes resolution for the artifact loader."""
from __future__ import annotations

import os
from urllib.parse import unquote

from aaa.platform.artifact_loader.errors import ArtifactUnavailable
from aaa.platform.evidence import EvidenceStore
from aaa.tools.client_doc_ingest import _coerce_bytes


def resolve_bytes(uri: str | None, store: EvidenceStore | None) -> bytes:
    """Resolve *uri* to raw bytes from the evidence store or local filesystem.

    Supports ``minio://`` (via the in-memory ``EvidenceStore``) and
    ``file://`` / bare local paths (for fixtures).

    :param uri: Artifact URI; empty values raise immediately.
    :param store: Evidence store used for ``minio://`` URIs.
    :returns: The raw artifact bytes — never ``None``.
    :raises ArtifactUnavailable: On any resolution miss.
    """
    if not uri:
        raise ArtifactUnavailable(uri, None, "empty or missing URI")

    if uri.startswith("minio://"):
        if store is None:
            raise ArtifactUnavailable(uri, None, "no evidence store supplied for minio:// URI")
        content = store.get_artefact(uri)
        if content is None:
            raise ArtifactUnavailable(uri, None, "URI not found in evidence store")
        return _coerce_bytes(content)

    if uri.startswith("file://") or os.path.isabs(uri) or os.path.exists(uri):
        path = uri[len("file://"):] if uri.startswith("file://") else uri
        path = unquote(path)
        try:
            with open(path, "rb") as handle:
                return handle.read()
        except OSError as exc:
            raise ArtifactUnavailable(uri, None, f"local file unreadable: {exc}") from exc

    raise ArtifactUnavailable(uri, None, "unsupported URI scheme")
