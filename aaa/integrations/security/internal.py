"""Internal security & robustness evidence, assembled from pipeline artefacts.

Robustness probing, output sampling (incl. prompt-injection suites for
LLM/agentic systems), and monitoring/logging review already run inside the
tier-2 phases; this adapter packages their artefact references into the
shared evidence document shape.
"""
from __future__ import annotations

from typing import Any

#: evidence key → phase-artefact id produced by the internal pipeline
_ARTEFACT_MAP = {
    "robustness_report": "T11_robustness_report",
    "output_sampling_log": "T13_output_sampling_log",
    "monitoring_logging_review": "T15_monitoring_logging_review",
}


class InternalSecurityProvider:
    """Packages internally-produced security/robustness artefact references."""

    def evaluate(self, state: dict[str, Any]) -> dict[str, Any]:
        """Assemble the evidence document from *state*'s phase artefacts.

        :param state: The audit state after the tier-2 phases ran.
        :type state: dict[str, Any]
        :returns: Evidence document with ``evidence_source: "internal"``.
        :rtype: dict[str, Any]
        """
        artefacts = state.get("phase_artefacts") or {}
        evidence: dict[str, Any] = {"evidence_source": "internal", "articles": ["Art.15"]}
        for key, artefact_id in _ARTEFACT_MAP.items():
            ref = artefacts.get(artefact_id)
            if isinstance(ref, dict):
                evidence[key] = ref
        return evidence
