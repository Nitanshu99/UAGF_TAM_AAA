"""Finding, verdict, and artefact-reference value types."""
from __future__ import annotations

from typing import Literal, Optional, TypedDict

#: The one materiality vocabulary. It was defined twice and the two disagreed:
#: here without ``observation``, in ``aaa.tools.findings`` without
#: ``not_material``, while six producers emit ``observation`` and the Verifier
#: prompt emits ``not_material``. Both lowest tiers are real and mean different
#: things to the article ladder (``supporting_tids._article_verdict``):
#:
#: * ``observation`` — a deterministic finding worth reporting; the article is
#:   at best PASS_WITH_OBSERVATIONS.
#: * ``not_material`` — an issue the Verifier assessed and judged immaterial; it
#:   does not qualify the article.
Materiality = Literal[
    "material",
    "possibly_material",
    "observation",
    "not_material",
]

#: e.g. "Art.9", "Art.43", "Annex_III"
Article = str

Verdict = Literal[
    "PASS", "PASS_WITH_OBSERVATIONS", "FAIL",
    "INSUFFICIENT_EVIDENCE", "NOT_APPLICABLE", "PENDING",
]


class AnnexIIIEntry(TypedDict):
    """One identified Annex III high-risk section with its provenance."""
    annex_iii_section: Literal["1", "2", "3", "4", "5", "6", "7", "8"]
    section_title: str
    use_case_marker: str
    confidence: float
    provenance: Literal["client_declared", "phase1_verified", "phase1_corrected", "phase1_rejected"]
    derogation_claimed: bool
    derogation_rationale: str | None


class Art43Decision(TypedDict):
    """Conformity-assessment procedure decision (§3.5)."""
    procedure: Literal["annex_vi_internal_control", "annex_vii_notified_body",
                       "annex_i_sectoral", "not_applicable"]
    rationale: str


class ArtefactRef(TypedDict):
    """Pointer to a stored template artefact."""
    uri: str
    sha256: str
    template_id: str


class Finding(TypedDict, total=False):
    """A single audit finding with materiality assessment."""
    finding_id: str
    phase: str
    phase_id: str
    article: str
    description: str
    severity: Literal["critical", "major", "minor", "observation"]
    materiality: Materiality
    materiality_rationale: str
    evidence_uri: Optional[str]
