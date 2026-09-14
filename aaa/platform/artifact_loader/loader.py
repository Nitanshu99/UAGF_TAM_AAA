"""Top-level URI → object loading for phase agents."""
from __future__ import annotations

from typing import Any

from aaa.platform.artifact_loader.deserialise import deserialise
from aaa.platform.artifact_loader.errors import KINDS, ArtifactUnavailable, infer_kind
from aaa.platform.artifact_loader.resolve import resolve_bytes
from aaa.platform.evidence import EvidenceStore


def load_artifact_from_uri(
    uri: str | None, store: EvidenceStore | None, kind: str | None = None,
) -> Any:
    """Resolve *uri* and deserialize it according to *kind*.

    :param uri: ``minio://`` or ``file://`` (or bare path) artifact reference.
    :param store: Evidence store used to resolve ``minio://`` URIs.
    :param kind: One of ``{joblib, csv, parquet, json, docx, text, bytes}``;
        inferred from the URI suffix when ``None``.
    :returns: The deserialized object — a fitted estimator (joblib), a
        ``pandas.DataFrame`` (csv/parquet), a ``dict``/``list`` (json),
        extracted text (docx/text), or raw ``bytes``.
    :raises ArtifactUnavailable: If the URI cannot be resolved or the payload
        cannot be deserialized.
    """
    resolved_kind = (kind or infer_kind(uri or "")).lower()
    if resolved_kind not in KINDS:
        raise ArtifactUnavailable(uri, resolved_kind, f"unknown artifact kind {resolved_kind!r}")

    # Fast path: a JSON artefact stored via ``store_artefact`` is already a dict —
    # avoid a needless bytes round-trip.
    if resolved_kind == "json" and uri and uri.startswith("minio://") and store is not None:
        content = store.get_artefact(uri)
        if content is None:
            raise ArtifactUnavailable(uri, resolved_kind, "URI not found in evidence store")
        if isinstance(content, (dict, list)) and not (
            isinstance(content, dict) and "body_base64" in content
        ):
            return content

    return deserialise(resolve_bytes(uri, store), resolved_kind, uri)
