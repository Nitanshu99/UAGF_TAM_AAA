"""Shared constants and KPI banding for Phase 6."""
from __future__ import annotations

PROMPT_NAME = "phase6_report"

#: Article → source phase mapping (populates ``T17.articles.source_phase``).
ARTICLE_PHASE: dict[str, str] = {
    "Art.5": "P1", "Art.6": "P1", "Art.9": "P5", "Art.10": "P2",
    # Art. 14 is Phase 5's: human oversight arrives as CGSA domain D5 inside
    # T14_governance_findings, not from model validation (fix 31).
    "Art.11": "P1", "Art.12": "P5", "Art.13": "P1", "Art.14": "P5",
    "Art.15": "P3", "Art.17": "P5", "Art.43": "P1", "Art.50": "P4",
    "Art.72": "P5", "Annex_III": "P1",
    "Annex_IV": "P1", "GPAI_51": "L", "GPAI_52": "L", "GPAI_53": "L",
    "GPAI_54": "L", "GPAI_55": "L", "Annex_XI": "L", "Annex_XII": "L",
}

VALID_PHASES = {"P1", "P2", "P3", "P4", "P5", "P6", "L", "CYBER", "PRIV", "ORCH"}

KPI_BANDS = [
    (0.90, "PASS"),
    (0.75, "PASS_WITH_OBSERVATIONS"),
    (0.0, "FAIL"),
]

METHODOLOGY_BASIS = (
    "This conformity assessment was conducted in accordance with the UAGF-TAM audit "
    "protocol (v1.0.0), applying the methodology of ISAE 3000 (Revised) for "
    "non-financial assurance engagements and ISO 19011:2018 for audit programme "
    "management. The audit was performed by an automated multi-agent system; results "
    "should be reviewed by a qualified human auditor before regulatory submission "
    "under Article 43 of the EU AI Act."
)


def kpi_band(value: float | None, pct: bool = False) -> str | None:
    """Map a KPI value onto its PASS / observations / FAIL band.

    :param value: KPI value, or ``None`` when not computed.
    :param pct: Whether *value* is a percentage (0–100) rather than a ratio.
    :returns: Band name, or ``None`` when the KPI was not computed.
    """
    if value is None:
        return None
    ratio = value / 100.0 if pct else value
    for threshold, band in KPI_BANDS:
        if ratio >= threshold:
            return band
    return "FAIL"
