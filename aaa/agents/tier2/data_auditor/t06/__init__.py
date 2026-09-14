"""T06 Datasheet for Datasets assembly (Gebru et al. structure)."""
from __future__ import annotations

from aaa.agents.tier2.data_auditor.dataset import dataset_role
from aaa.agents.tier2.data_auditor.t06.cited import NOT_DECLARED, Found
from aaa.agents.tier2.data_auditor.t06.instances import instances_type
from aaa.agents.tier2.data_auditor.t06.measured import DatasetMeasurement, measure
from aaa.agents.tier2.data_auditor.t06.notes import art10_notes
from aaa.agents.tier2.data_auditor.t06.questions import t06_questions
from aaa.agents.tier2.data_auditor.t06.sections import (
    collection_section,
    composition_section,
    motivation_section,
)
from aaa.agents.tier2.data_auditor.t06.tail import (
    distribution_section,
    maintenance_section,
    preprocessing_section,
    uses_section,
)
from aaa.tools.data_dictionary import explicit_data_dictionary


def build_t06(engagement_id: str, t01a: dict, t01b: dict, decl: dict, now: str,
              measured: DatasetMeasurement | None = None, found: Found | None = None,
              label_bias: dict | None = None) -> dict:
    """Build T06 from what Phase 2 measured and what the dossier declares.

    :param engagement_id: Engagement identifier.
    :param t01a: Stage A triage payload.
    :param t01b: Annex IV dossier.
    :param decl: Declaration summary (provider-name fallback, Stage B).
    :param now: ISO-8601 generation timestamp.
    :param measured: The dataset Phase 2 loaded, or ``None`` when none was.
    :param found: Grounded answers to :func:`t06_questions`; ``None`` when none were sought.
    :param label_bias: Phase 2's label-disparity measurement, when one was taken.
    :returns: The T06 payload matching the template schema.
    """
    provider = t01a.get("provider_name") or decl.get("provider_name") or NOT_DECLARED
    training_desc = t01b.get("training_data_description") or NOT_DECLARED
    dictionary = explicit_data_dictionary(decl.get("stage_b") or t01b or {})
    found = found or {}
    return {
        "engagement_id": engagement_id,
        "motivation": motivation_section(t01a, provider),
        "composition": composition_section(
            t01a, instances_type(training_desc, measured, dataset_role(t01b, decl),
                                 dictionary.get("target_column")),
            dictionary, measured, found),
        "collection_process": collection_section(found),
        "preprocessing_cleaning_labelling": preprocessing_section(found),
        "uses": uses_section(t01a, label_bias),
        "distribution": distribution_section(t01a),
        "maintenance": maintenance_section(t01a, provider, found),
        "art10_compliance_notes": art10_notes(dictionary, measured, found),
        "generated_at": now,
    }


__all__ = ["DatasetMeasurement", "Found", "build_t06", "measure", "t06_questions"]
