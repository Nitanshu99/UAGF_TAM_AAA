"""The Art. 10 notes that say where each T06 value came from."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.data_auditor.declared_counts import counts_phrase
from aaa.agents.tier2.data_auditor.t06.cited import Found, grounded
from aaa.agents.tier2.data_auditor.t06.gaps import undeclared_note
from aaa.agents.tier2.data_auditor.t06.measured import DatasetMeasurement


def art10_notes(dictionary: dict[str, Any], measured: DatasetMeasurement | None,
                found: Found | None = None) -> str:
    """Provenance of the datasheet's counts, declarations and quotations.

    :param dictionary: The declared data dictionary.
    :param measured: What Phase 2 measured, or ``None``.
    :param found: The grounded document answers the datasheet quotes.
    :returns: The ``art10_compliance_notes`` text, before the prompt note.
    """
    if measured is None:
        parts = ["No dataset could be loaded, so composition counts are null rather "
                 "than estimated."]
    else:
        parts = [f"Composition measured on {measured.dataset_uri}: "
                 f"{counts_phrase(measured, dictionary.get('target_column'))}."]
        absent = [c for c in dictionary.get("sensitive_feature_columns") or []
                  if str(c) not in measured.columns]
        if absent:
            parts.append("Declared sensitive columns absent from that dataset: "
                         f"{', '.join(map(str, absent))}.")
    quoted = grounded(found or {})
    parts.append("instances_type names the dataset examined and quotes the declared "
                 "training_data_description as a separate dataset where they differ. "
                 + (f"Quoted from the provider's documents, as stated and not verified: "
                    f"{', '.join(quoted)}. " if quoted else "")
                 + "Fields no dossier field or document passage answers are null or "
                   "recorded as not declared.")
    parts.append(undeclared_note(found or {}))
    return " ".join(p for p in parts if p) + " Phase 2 DataAuditor — Art. 10 §2–§3."


__all__ = ["art10_notes"]
