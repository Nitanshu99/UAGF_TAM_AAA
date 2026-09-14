"""intake_completeness_calculator — deterministic MCP-style tool.

Computes KPI 0: `intake_completeness_score` (0.0–1.0) from the
populated Annex IV §1–§9 bundle (T01b) in a ClientSubmission.

The section weights and gate threshold (0.80) are the authoritative
reference from §9.1 of ARCHITECTURE.md.  Any change to either value
requires a new semver tag on uagf-tam-templates and supervisor sign-off.

Usage (§4.5):
    report = intake_completeness_calculator(submission, declared_modality)
    state["intake_completeness_score"] = report.score"""
from aaa.tools.intake_completeness_calculator.core import (  # noqa: F401
    intake_completeness_calculator,
)
from aaa.tools.intake_completeness_calculator.field_present import (  # noqa: F401
    _field_present,
    _score_sections,
)
from aaa.tools.intake_completeness_calculator.missingfield import (  # noqa: F401
    CompletenessReport,
    ConditionalField,
    MissingField,
)
from aaa.tools.intake_completeness_calculator.section_weights import (  # noqa: F401
    _L_BRANCH_CONDITIONAL,
    _L_BRANCH_MODALITIES,
    _SECTION_FIELDS,
    GATE_THRESHOLD,
    SECTION_WEIGHTS,
    SectionScore,
)

__all__ = [
    'SECTION_WEIGHTS', 'GATE_THRESHOLD', '_SECTION_FIELDS', '_L_BRANCH_CONDITIONAL', '_L_BRANCH_MODALITIES',
    'SectionScore', 'MissingField', 'ConditionalField', 'CompletenessReport', '_field_present',
    '_score_sections', 'intake_completeness_calculator',
]
