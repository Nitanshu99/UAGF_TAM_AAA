"""
intake_completeness_calculator — deterministic MCP-style tool.

Computes KPI 0: `intake_completeness_score` (0.0–1.0) from the
populated Annex IV §1–§9 bundle (T01b) in a ClientSubmission.

The section weights and gate threshold (0.80) are the authoritative
reference from §9.1 of ARCHITECTURE.md.  Any change to either value
requires a new semver tag on uagf-tam-templates and supervisor sign-off.

Usage (§4.5):
    report = intake_completeness_calculator(submission, declared_modality)
    state["intake_completeness_score"] = report.score
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aaa.platform.state import AnnexIVDossier, ClientSubmission

# ── Section weights (§9.1) ────────────────────────────────────────────────────
SECTION_WEIGHTS: dict[int, float] = {
    1: 0.20,  # General description
    2: 0.15,  # Design and development
    3: 0.10,  # Monitoring and control
    4: 0.15,  # Performance metrics
    5: 0.15,  # Risk management (Art. 9)
    6: 0.05,  # Lifecycle changes
    7: 0.10,  # Standards applied
    8: 0.05,  # EU declaration of conformity
    9: 0.05,  # Post-market monitoring plan
}

GATE_THRESHOLD = 0.80

# ── Field → section mapping ───────────────────────────────────────────────────
_SECTION_FIELDS: dict[int, list[str]] = {
    1: ["general_description", "model_type"],
    2: ["design_process", "training_data_description", "data_governance_measures"],
    3: ["monitoring_measures", "logging_capabilities"],
    4: ["accuracy_metrics"],
    5: ["risk_management_file_uri"],
    6: ["lifecycle_change_log"],
    7: ["harmonised_standards"],
    8: ["eu_doc_uri"],
    9: ["post_market_plan_uri"],
}

_L_BRANCH_CONDITIONAL: dict[str, str] = {
    "system_prompt_uri": "llm/agentic/gpai",
    "rag_manifest_uri": "llm/agentic/gpai",
    "guardrail_config_uri": "llm/agentic/gpai",
    "golden_set_uri": "llm/agentic/gpai",
    "tool_inventory": "agentic",
}

_L_BRANCH_MODALITIES = {"llm", "agentic", "gpai"}


@dataclass
class SectionScore:
    score: float
    weight: float
    label: str


@dataclass
class MissingField:
    field: str
    section: int
    reason: str


@dataclass
class ConditionalField:
    field: str
    condition: str
    applicable: bool


@dataclass
class CompletenessReport:
    """Output contract for intake_completeness_calculator."""
    engagement_id: str
    score: float
    section_scores: dict[str, SectionScore]
    missing_required: list[MissingField]
    missing_conditional: list[ConditionalField]
    gate_passed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "engagement_id": self.engagement_id,
            "intake_completeness_score": self.score,
            "section_scores": {
                k: {"score": v.score, "weight": v.weight, "label": v.label}
                for k, v in self.section_scores.items()
            },
            "missing_required_fields": [
                {"field": f.field, "section": f.section, "reason": f.reason}
                for f in self.missing_required
            ],
            "missing_conditional_fields": [
                {"field": f.field, "condition": f.condition, "applicable": f.applicable}
                for f in self.missing_conditional
            ],
            "gate_passed": self.gate_passed,
        }


def intake_completeness_calculator(
    submission: ClientSubmission,
    declared_modality: str,
    engagement_id: str = "",
) -> CompletenessReport:
    """
    Computes the weighted Annex IV completeness score (KPI 0).

    Args:
        submission: The full ClientSubmission (Stage A + B).
        declared_modality: Modality declared in Stage A.
        engagement_id: Engagement identifier for the report.

    Returns:
        CompletenessReport with .score and .gate_passed.
    """
    dossier = submission["stage_b"]
    is_l_branch = declared_modality in _L_BRANCH_MODALITIES
    is_agentic = declared_modality == "agentic"

    section_scores: dict[str, SectionScore] = {}
    missing_required: list[MissingField] = []
    total_score = 0.0

    for section, fields in _SECTION_FIELDS.items():
        weight = SECTION_WEIGHTS[section]
        present = [f for f in fields if _field_present(dossier, f)]
        frac = len(present) / len(fields) if fields else 1.0
        total_score += weight * frac
        section_scores[str(section)] = SectionScore(
            score=round(frac, 4),
            weight=weight,
            label=f"Annex IV §{section}",
        )
        for f in fields:
            if not _field_present(dossier, f):
                missing_required.append(MissingField(field=f, section=section, reason="Empty or missing"))

    missing_conditional: list[ConditionalField] = []
    for fname, condition in _L_BRANCH_CONDITIONAL.items():
        applicable = is_l_branch if "agentic" not in condition else is_agentic
        present = _field_present(dossier, fname)
        missing_conditional.append(ConditionalField(field=fname, condition=condition, applicable=applicable))
        if applicable and not present:
            # Conditional required fields reduce the score by their section weight / n_fields
            total_score = max(0.0, total_score - 0.02)

    score = round(min(total_score, 1.0), 2)
    return CompletenessReport(
        engagement_id=engagement_id,
        score=score,
        section_scores=section_scores,
        missing_required=missing_required,
        missing_conditional=missing_conditional,
        gate_passed=score >= GATE_THRESHOLD,
    )


def _field_present(dossier: dict[str, Any], field_name: str) -> bool:
    val = dossier.get(field_name)
    if val is None:
        return False
    if isinstance(val, (str, list, dict)):
        return bool(val)
    return True
