"""Evidence store — artefact and file persistence with provenance metadata.

The demo implementation keeps everything in process memory but issues
MinIO-style URIs so the storage backend can be swapped without touching
call sites.
"""
from __future__ import annotations

from aaa.platform.evidence.store import EvidenceStore

__all__ = ["EvidenceStore"]
