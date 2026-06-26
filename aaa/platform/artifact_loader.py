"""
aaa.platform.artifact_loader — Resolve evidence-store URIs to concrete artifacts.

Phase agents must independently re-run analysis on the *real* client artifacts
(model ``.joblib``, training / evaluation CSVs, ``.docx`` governance documents)
rather than trusting declared values. This module resolves a stored URI to a
deserialized object, reusing the base64 body-encoding that
:meth:`EvidenceStore.store_file` writes and the docx text extractor already proven
in :mod:`aaa.tools.client_doc_ingest`.

Design contract (deliberately different from the rest of the codebase): a failure
to obtain a *required* artifact raises :class:`ArtifactUnavailable` instead of
returning a silent ``None`` / empty frame. Callers translate that into an
``INSUFFICIENT_EVIDENCE`` verdict for the affected EU AI Act article, so a missing
model can never masquerade as a PASS.
"""
from __future__ import annotations

import io
import json
import logging
import os
from typing import Any
from urllib.parse import unquote, urlparse

from aaa.platform.evidence import EvidenceStore
from aaa.tools.client_doc_ingest import _coerce_bytes, _extract_docx_pages

logger = logging.getLogger(__name__)

# Recognised deserialisation targets.
_KINDS = {"joblib", "csv", "parquet", "json", "docx", "text", "bytes"}

# URI suffix → default kind (used by :func:`infer_kind`).
_SUFFIX_KIND = {
    ".joblib": "joblib",
    ".pkl": "joblib",
    ".pickle": "joblib",
    ".csv": "csv",
    ".tsv": "csv",
    ".parquet": "parquet",
    ".json": "json",
    ".docx": "docx",
    ".txt": "text",
    ".md": "text",
}


class ArtifactUnavailable(Exception):
    """Raised when a required artifact cannot be resolved or deserialized.

    Carries enough context for a phase agent to record *why* an article is being
    downgraded to INSUFFICIENT_EVIDENCE.
    """

    def __init__(self, uri: str | None, kind: str | None, reason: str):
        self.uri = uri
        self.kind = kind
        self.reason = reason
        super().__init__(f"[artifact_loader] {reason} (uri={uri!r}, kind={kind!r})")


def infer_kind(uri: str) -> str:
    """Best-effort kind inference from a URI's file extension; defaults to ``bytes``."""
    name = urlparse(uri).path if "://" in uri else uri
    for suffix, kind in _SUFFIX_KIND.items():
        if name.lower().endswith(suffix):
            return kind
    return "bytes"


def resolve_bytes(uri: str | None, store: EvidenceStore | None) -> bytes:
    """Resolve ``uri`` to raw bytes from the evidence store or local filesystem.

    Supports ``minio://`` (via the in-memory ``EvidenceStore``) and ``file://`` /
    bare local paths (for fixtures). Raises :class:`ArtifactUnavailable` on any
    miss — never returns ``None``.
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


def load_artifact_from_uri(
    uri: str | None,
    store: EvidenceStore | None,
    kind: str | None = None,
) -> Any:
    """Resolve ``uri`` and deserialize it according to ``kind``.

    Parameters
    ----------
    uri:
        ``minio://`` or ``file://`` (or bare path) reference to the artifact.
    store:
        Evidence store used to resolve ``minio://`` URIs.
    kind:
        One of ``{joblib, csv, parquet, json, docx, text, bytes}``. If ``None``,
        inferred from the URI suffix.

    Returns
    -------
    The deserialized object: a fitted estimator (joblib), a ``pandas.DataFrame``
    (csv/parquet), a ``dict``/``list`` (json), extracted text (docx/text), or raw
    ``bytes``.

    Raises
    ------
    ArtifactUnavailable
        If the URI cannot be resolved or the payload cannot be deserialized.
    """
    resolved_kind = (kind or infer_kind(uri or "")).lower()
    if resolved_kind not in _KINDS:
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

    data = resolve_bytes(uri, store)

    try:
        if resolved_kind == "bytes":
            return data
        if resolved_kind == "text":
            return data.decode("utf-8", errors="replace")
        if resolved_kind == "json":
            return json.loads(data.decode("utf-8"))
        if resolved_kind == "docx":
            pages = _extract_docx_pages(data)
            return "\n".join(text for _, text in pages if text)
        if resolved_kind == "joblib":
            try:
                import joblib  # type: ignore
            except ImportError as exc:  # pragma: no cover - environment gap
                raise ArtifactUnavailable(uri, resolved_kind, "joblib not installed") from exc
            return joblib.load(io.BytesIO(data))
        if resolved_kind == "csv":
            import pandas as pd
            sep = "\t" if (uri or "").lower().endswith(".tsv") else ","
            return pd.read_csv(io.BytesIO(data), sep=sep)
        if resolved_kind == "parquet":
            import pandas as pd
            return pd.read_parquet(io.BytesIO(data))
    except ArtifactUnavailable:
        raise
    except Exception as exc:  # noqa: BLE001 - any deserialisation failure → unavailable
        raise ArtifactUnavailable(
            uri, resolved_kind, f"deserialisation failed: {type(exc).__name__}: {exc}"
        ) from exc

    raise ArtifactUnavailable(uri, resolved_kind, "unreachable kind dispatch")


__all__ = ["ArtifactUnavailable", "load_artifact_from_uri", "resolve_bytes", "infer_kind"]
