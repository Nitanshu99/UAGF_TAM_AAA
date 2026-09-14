"""aaa.platform.artifact_loader — Resolve evidence-store URIs to artifacts.

Phase agents must independently re-run analysis on the *real* client
artifacts (model ``.joblib``, training / evaluation CSVs, ``.docx``
governance documents) rather than trusting declared values.

Design contract: a failure to obtain a *required* artifact raises
:class:`ArtifactUnavailable` instead of returning a silent ``None`` — callers
translate that into an ``INSUFFICIENT_EVIDENCE`` verdict for the affected
EU AI Act article, so a missing model can never masquerade as a PASS.
"""
from __future__ import annotations

from aaa.platform.artifact_loader.errors import ArtifactUnavailable, infer_kind
from aaa.platform.artifact_loader.loader import load_artifact_from_uri
from aaa.platform.artifact_loader.resolve import resolve_bytes

__all__ = ["ArtifactUnavailable", "load_artifact_from_uri", "resolve_bytes", "infer_kind"]
