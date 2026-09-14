"""cgsa_ingest — validate the pulled CGSA payload and map every §5.4 field
into the AAA ``AuditState`` (§4.5).

Workflow:

  1. ``schema_validate(payload, "1.0.0")`` against the vendored
     ``schemas/cgsa/v1.0.0/uagf_cgsa_aaa_schema.json`` (§10.2 canonical path).
     Failure ⇒ raises ``CGSAIngestError`` so the GovernanceAgent can ``escalate_hitl``.
  2. Map the payload into the typed ``CGSAPayload`` shape (§5.4
     consumption map — every required field is consumed, nothing dropped).
  3. Surface low-confidence controls (``confidence < 0.6``) and CSP
     failures (``csp_satisfiable = false``) for downstream HITL flagging.

The function returns an ``IngestResult`` dataclass containing both the
validated payload and a ``state_delta`` dict ready to be merged into
``AuditState``."""
from aaa.tools.cgsa_ingest.aggregate_low_confidence import _aggregate_low_confidence  # noqa: F401
from aaa.tools.cgsa_ingest.build_state_delta import _build_state_delta  # noqa: F401
from aaa.tools.cgsa_ingest.core import cgsa_ingest  # noqa: F401
from aaa.tools.cgsa_ingest.logger import (  # noqa: F401
    _LOW_CONFIDENCE_THRESHOLD,
    _REQUIRED_TOP_LEVEL_KEYS,
    _VENDORED_SCHEMA,
    CGSAIngestError,
    IngestResult,
    logger,
)
from aaa.tools.cgsa_ingest.normalise_remediation import (  # noqa: F401
    _infer_harmonised_standards,
    _normalise_remediation,
)
from aaa.tools.cgsa_ingest.risk_tier_match import _risk_tier_match  # noqa: F401
from aaa.tools.cgsa_ingest.schema_validate import schema_validate  # noqa: F401
from aaa.tools.cgsa_ingest.shallow_required_check import _shallow_required_check  # noqa: F401

__all__ = [
    'logger', '_VENDORED_SCHEMA', '_LOW_CONFIDENCE_THRESHOLD', '_REQUIRED_TOP_LEVEL_KEYS',
    'CGSAIngestError', 'IngestResult', '_shallow_required_check', 'schema_validate', '_aggregate_low_confidence',
    '_normalise_remediation', '_infer_harmonised_standards', '_build_state_delta', '_risk_tier_match',
    'cgsa_ingest',
]
