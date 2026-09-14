"""Typed state contracts shared across the AAA pipeline (§5.1, §5.4, §6).

Every intake, CGSA, finding, and audit-state type is re-exported here so
callers keep importing from ``aaa.platform.state``.
"""
from __future__ import annotations

from aaa.platform.state.audit_state import AuditState, DocExtractionResult
from aaa.platform.state.audit_state.compliance import AuditStateCompliance
from aaa.platform.state.audit_state.parts import AuditStateCGSA, AuditStateIdentity
from aaa.platform.state.cgsa import (
    BlockingFinding,
    FollowUpItem,
    LowConfidenceControl,
    PositiveFinding,
    RemediationItem,
)
from aaa.platform.state.cgsa.payload import (
    CGSAAAPhase5Handoff,
    CGSAMetadata,
    CGSAOverallScores,
    CGSAPayload,
)
from aaa.platform.state.dossier import AnnexIVDossier, ClientSubmission, StageCAccess
from aaa.platform.state.findings import (
    AnnexIIIEntry,
    Art43Decision,
    ArtefactRef,
    Article,
    Finding,
    Materiality,
    Verdict,
)
from aaa.platform.state.intake import StageATriage
from aaa.platform.state.verdicts import (
    ASSESSED_ARTICLE_VERDICTS,
    DISCLAIMER_OF_OPINION,
    FINAL_VERDICTS,
    FinalVerdict,
)

__all__ = [
    "ASSESSED_ARTICLE_VERDICTS", "DISCLAIMER_OF_OPINION", "FINAL_VERDICTS",
    "FinalVerdict",
    "AnnexIIIEntry", "AnnexIVDossier", "Art43Decision", "ArtefactRef", "Article",
    "AuditState", "AuditStateCGSA", "AuditStateCompliance", "AuditStateIdentity",
    "BlockingFinding", "CGSAAAPhase5Handoff", "CGSAMetadata", "CGSAOverallScores",
    "CGSAPayload", "ClientSubmission", "DocExtractionResult", "Finding",
    "FollowUpItem", "LowConfidenceControl", "Materiality", "PositiveFinding",
    "RemediationItem", "StageATriage", "StageCAccess", "Verdict",
]
