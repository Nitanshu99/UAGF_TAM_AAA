"""Part 7 of the former ``cgsa_ingest`` module (auto-split)."""
from __future__ import annotations

from aaa.tools.cgsa_ingest.aggregate_low_confidence import _aggregate_low_confidence  # noqa: F401
from aaa.tools.cgsa_ingest.build_state_delta import _build_state_delta  # noqa: F401
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
from aaa.tools.cgsa_ingest.schema_validate import schema_validate  # noqa: F401
from aaa.tools.cgsa_ingest.shallow_required_check import _shallow_required_check  # noqa: F401


def _risk_tier_match(phase1_risk_tier: str | None,
                     cgsa_risk_tier: str | None) -> bool | None:
    """Cross-check the Phase 1 risk tier against CGSA metadata.

    :returns: ``True``/``False`` when both sides are present, else ``None``.
    """
    if phase1_risk_tier is None or cgsa_risk_tier is None:
        return None
    return phase1_risk_tier == cgsa_risk_tier
