"""AuditState — full LangGraph typed dict threaded through the graph (§5.1)."""
from __future__ import annotations

from typing import Any, TypedDict

from aaa.platform.state.audit_state.compliance import AuditStateCompliance
from aaa.platform.state.audit_state.evidence import AuditStateEvidence
from aaa.platform.state.audit_state.parts import AuditStateCGSA, AuditStateIdentity


class DocExtractionResult(TypedDict):
    """Result returned by DocIntelligenceAgent after reading customer uploads."""
    stage_a_partial: dict[str, Any]
    stage_b_partial: dict[str, Any]
    field_confidence: dict[str, float]   # field_name → 0.0–1.0
    field_sources: dict[str, str]        # field_name → "filename, p. N"
    missing_fields: list[str]
    #: Why the extraction returned what it did (M23). ``ok`` means the agent
    #: read the documents and reported on every field; every other value is a
    #: system failure, and ``missing_fields`` then says nothing about whether
    #: the information is in the customer's documents.
    extraction_status: str


class AuditState(AuditStateIdentity, AuditStateCGSA, AuditStateCompliance,
                 AuditStateEvidence):
    """The complete engagement state — union of the four section TypedDicts.

    Sections (see :mod:`aaa.platform.state.audit_state.parts`):

    * :class:`AuditStateIdentity` — engagement identity, declared values,
      Phase 1 verified values, artefact graph.
    * :class:`AuditStateCGSA` — the S4 CGSA hand-off surface (§5.4).
    * :class:`AuditStateCompliance` — compliance assembly, verification,
      and the final verdict.
    * :class:`AuditStateEvidence` — XAI / security evidence landing zone
      (:mod:`aaa.platform.state.audit_state.evidence`).
    """
