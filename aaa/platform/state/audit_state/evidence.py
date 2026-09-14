"""Evidence landing zone for the switchable XAI / security providers.

Populated by :mod:`aaa.integrations` regardless of mode; the report and the
results UI render these documents source-agnostically (customers never see
which provider produced them).
"""
from __future__ import annotations

from typing import Any, Literal, NotRequired, Optional, TypedDict

#: "not_required" — the audit scope does not call for this evidence
#: (aaa.integrations.gating); never rendered as a gap or a missing artefact.
EvidenceSource = Literal["internal", "external", "not_required"]


class AuditStateEvidence(TypedDict):
    """Explainability/fairness and security/robustness evidence documents."""

    xai_evidence: NotRequired[Optional[dict[str, Any]]]
    xai_evidence_source: NotRequired[Optional[EvidenceSource]]
    security_evidence: NotRequired[Optional[dict[str, Any]]]
    security_evidence_source: NotRequired[Optional[EvidenceSource]]
    # How each protected attribute was actually grouped before a fairness metric
    # saw it — binned or not, how many cohorts, the smallest, and whether the
    # attribute was testable at all (fix F11). The same record T12 carries,
    # promoted onto the state so the S6 hand-off can ship it without resolving
    # an artefact URI. A consumer holding only `sensitive_feature_columns` sees
    # names and has to guess; that guess is finding S18.
    sensitive_feature_groups: NotRequired[Optional[list[dict[str, Any]]]]
