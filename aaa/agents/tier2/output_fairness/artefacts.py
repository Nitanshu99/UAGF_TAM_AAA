"""Building and storing the Phase 4 artefacts (T12 / T13)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from aaa.agents.tier2.output_fairness.context import FairnessInputs, LlmSynthesis, SuiteResult
from aaa.agents.tier2.output_fairness.t12 import build_t12
from aaa.agents.tier2.output_fairness.t13 import build_t13
from aaa.tools.regulatory_coverage.binding_notes import annotate_non_binding


def build_and_store_artefacts(
    agent: Any,
    engagement_id: str,
    modality: str,
    inp: FairnessInputs,
    suite: SuiteResult,
    tox_result: dict[str, Any],
    skipped_reason: str | None,
    llm: LlmSynthesis,
    risk_tier: str | None = None,
) -> tuple[dict[str, str], dict[str, Any]]:
    """Build T12 / T13, annotate them, and write to the Evidence Store.

    :param agent: The calling :class:`OutputFairnessTester` instance.
    :param engagement_id: Engagement identifier.
    :param modality: Normalised system modality.
    :param inp: Resolved Phase 4 inputs.
    :param suite: Fairness suite result.
    :param tox_result: ``toxicity_classifier`` result.
    :param skipped_reason: Why the suite was skipped, if it was.
    :param llm: LLM synthesis outcome (summary + prompt note).
    :returns: ``(uris, t13)`` — artefact URIs keyed by template id, and the
        T13 content needed for the discriminatory-pattern flag downstream.
    """
    now = datetime.now(timezone.utc).isoformat()
    t12 = build_t12(engagement_id, modality, inp, suite, skipped_reason, now)
    t13 = build_t13(engagement_id, modality, inp, tox_result, now, skipped_reason)
    # A measurement narrative is built from this artefact's own fields. The LLM's
    # reply summarises the whole phase and quoted numbers the artefact does not hold —
    # T11 carried metric-suite accuracy and SHAP values beside its probe fields, and
    # the Verifier refused it (case 03, T-20260913-067). It stays the Report summary.
    t12["fairness_narrative"] = f"{t12['fairness_narrative']} {llm.prompt_note}".strip()
    t13["sampling_narrative"] = f"{t13['sampling_narrative']} {llm.prompt_note}".strip()
    for payload in (t12, t13):
        annotate_non_binding(payload, risk_tier)
    uris = {
        template_id: agent.store.store_artefact(
            engagement_id, "phase_4", template_id, content, agent.name)
        for template_id, content in (("T12_output_fairness_report", t12),
                                     ("T13_output_sampling_log", t13))
    }
    return uris, t13
