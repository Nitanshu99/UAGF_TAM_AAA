"""Internal explainability & fairness evidence, assembled from pipeline artefacts.

The tier-2 agents (model_validator, output_fairness) already produce the
T09–T13 artefacts; this adapter packages their references into the shared
evidence document shape so reports render source-agnostically.
"""
from __future__ import annotations

from typing import Any

#: evidence key → phase-artefact id produced by the internal pipeline
_ARTEFACT_MAP = {
    "model_card": "T09_model_card",
    "explainability_report": "T10_explainability_report",
    "fairness_report": "T12_output_fairness_report",
    "output_sampling_log": "T13_output_sampling_log",
}


class InternalXAIProvider:
    """Packages internally-produced explainability/fairness artefact references."""

    def evaluate(self, state: dict[str, Any]) -> dict[str, Any]:
        """Assemble the evidence document from *state*'s phase artefacts.

        :param state: The audit state after the tier-2 phases ran.
        :type state: dict[str, Any]
        :returns: Evidence document with ``evidence_source: "internal"``.
        :rtype: dict[str, Any]
        """
        artefacts = state.get("phase_artefacts") or {}
        evidence: dict[str, Any] = {"evidence_source": "internal", "articles": ["Art.13"]}
        for key, artefact_id in _ARTEFACT_MAP.items():
            ref = artefacts.get(artefact_id)
            if isinstance(ref, dict):
                evidence[key] = ref
        return evidence
