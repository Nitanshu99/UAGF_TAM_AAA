"""Derive ``component_modalities`` for a composite system (§6.2 routing).

The phase plan is solved **once**, from the declaration, before Phase 1
dispatches. ``build_phase_csp`` skips Phases 3 and 4 — model validation and
output fairness — when no declared component ranks, scores or classifies. That
is right for a system that really is only a language model, and wrong for a
composite one: a ranking model beside a generative model attracts both.

The wizard has never been able to say a system is composite. ``collect_stage_a``
builds the declaration field by field and ``component_modalities`` was not among
them, so case 06 audited through the wizard returned 57.1 % coverage against the
100 % of the same case submitted whole through the API — with two phases
missing and nothing saying so.

Two ways out, used together here:

* what the customer **says**, from the step-2 question (authoritative); and
* what the dossier **shows** — a system reporting precision@k and nDCG@k over an
  evaluation dataset is ranking something, whatever its modality field says.

A derived component can only *add* obligations: ``merge_requirements`` takes the
stronger status per phase, so a false positive audits more, never less. It is
written into Stage A with a ``role`` that says where it came from, so the
Verifier, the system card and the client brief all see an inference rather than
a fact the customer asserted.
"""
from __future__ import annotations

import json
from typing import Any

from aaa.ui.wizard.collect.metric_names import _DISCRIMINATIVE_METRIC


def _metric_names(raw: Any) -> list[str]:
    """Metric keys from the Stage B performance block, however it is shaped."""
    if isinstance(raw, str):
        try:
            raw = json.loads(raw or "{}")
        except json.JSONDecodeError:
            return []
    if not isinstance(raw, dict):
        return []
    names = [k for k in raw if not isinstance(raw.get(k), dict)]
    for nested in ("accuracy_metrics", "robustness_metrics", "fairness_metrics"):
        block = raw.get(nested)
        if isinstance(block, dict):
            names.extend(block)
    return names


def discriminative_evidence(stage_b: dict[str, Any]) -> list[str]:
    """Signals in the dossier that the system ranks, scores or classifies.

    :param stage_b: The Stage B payload (or its in-progress session form).
    :returns: Human-readable reasons, empty when nothing indicates it.
    """
    reasons: list[str] = []
    metrics = [m for m in _metric_names(stage_b.get("accuracy_metrics"))
               if _DISCRIMINATIVE_METRIC.match(str(m))]
    if metrics:
        reasons.append("ranking/classification metrics (" + ", ".join(sorted(metrics)[:4]) + ")")
    if any(stage_b.get(f) for f in ("target_column", "positive_label",
                                    "sensitive_feature_columns")):
        reasons.append("a declared prediction target or protected attribute")
    if stage_b.get("model_artifact_uri"):
        reasons.append("a supplied model artefact")
    elif stage_b.get("evaluation_dataset_uri") and metrics:
        reasons.append("an evaluation dataset those metrics are computed over")
    return reasons




__all__ = ["discriminative_evidence"]
