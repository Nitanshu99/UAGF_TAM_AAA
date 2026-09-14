"""KPI 1 — Completeness Score (§9.1)

Fraction of expected artefact templates that are present, schema-valid, and
admitted by the Verifier for the given engagement.

  expected = {tid : status in {M, O} from phase_status CSP output}
  delivered = {tid : verifier verdict in {accept, accept_with_notes}}
  score = |delivered ∩ expected| / max(|expected|, 1)

Mandatory templates (status=M) have weight 1.0; optional (status=O) weight 0.5.
Written to AuditState.completeness_score."""
from aaa.tools.completeness_score.admitted_verdicts import (  # noqa: F401
    _ADMITTED_VERDICTS,
    _STATUS_WEIGHT,
    compute_completeness_score,
)
from aaa.tools.completeness_score.completeness_score_breakdown import (  # noqa: F401
    completeness_score_breakdown,
)

__all__ = [
    '_ADMITTED_VERDICTS',
    '_STATUS_WEIGHT',
    'compute_completeness_score',
    'completeness_score_breakdown',
]
