"""Artifact-loader error type and kind inference."""
from __future__ import annotations

from urllib.parse import urlparse

#: Recognised deserialisation targets.
KINDS = {"joblib", "csv", "parquet", "json", "docx", "text", "bytes"}

#: URI suffix → default kind (used by :func:`infer_kind`).
SUFFIX_KIND = {
    ".joblib": "joblib", ".pkl": "joblib", ".pickle": "joblib",
    ".csv": "csv", ".tsv": "csv", ".parquet": "parquet", ".json": "json",
    ".docx": "docx", ".txt": "text", ".md": "text",
}


class ArtifactUnavailable(Exception):  # noqa: N818  (established public name)
    """Raised when a required artifact cannot be resolved or deserialized.

    Carries enough context for a phase agent to record *why* an article is
    being downgraded to INSUFFICIENT_EVIDENCE.
    """

    def __init__(self, uri: str | None, kind: str | None, reason: str):
        self.uri = uri
        self.kind = kind
        self.reason = reason
        super().__init__(f"[artifact_loader] {reason} (uri={uri!r}, kind={kind!r})")


def infer_kind(uri: str) -> str:
    """Best-effort kind inference from a URI's file extension.

    :param uri: Artifact URI or bare path.
    :returns: A kind from :data:`KINDS`; defaults to ``"bytes"``.
    """
    name = urlparse(uri).path if "://" in uri else uri
    for suffix, kind in SUFFIX_KIND.items():
        if name.lower().endswith(suffix):
            return kind
    return "bytes"
