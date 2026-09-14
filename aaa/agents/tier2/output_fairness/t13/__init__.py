"""T13 output sampling log builder."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.output_fairness.context import FairnessInputs
from aaa.agents.tier2.output_fairness.t13.notes import art10_2f_note, sampling_narrative
from aaa.agents.tier2.output_fairness.t13.sample import build_predictions_sample
from aaa.agents.tier2.output_fairness.toxicity import outputs_are_text


def build_t13(engagement_id: str, modality: str, inp: FairnessInputs,
              tox_result: dict[str, Any], now: str,
              skipped_reason: str | None = None) -> dict[str, Any]:
    """Build the T13 output sampling log.

    :param engagement_id: Engagement identifier.
    :param modality: Normalised system modality.
    :param inp: Resolved Phase 4 inputs.
    :param tox_result: ``toxicity_classifier`` result.
    :param now: ISO-8601 generation timestamp.
    :param skipped_reason: Why Phase 4 had nothing to test, when it had nothing.
    :returns: T13 sampling-log dictionary.
    """
    predictions_sample = build_predictions_sample(inp)
    flagged = [e for e in tox_result.get("entries", []) if e.get("flagged")]
    examples = [{"prediction_id": e["prediction_id"],
                 "category": (e.get("flagged_categories") or ["unknown"])[0],
                 "excerpt": e.get("text_excerpt")}
                for e in flagged[:10]]
    screened = tox_result.get("verdict") != "NOT_TESTED"
    # Unscreened is unknown, not "no pattern" (T-20260913-107).
    discriminatory = bool(flagged) if screened else None
    if tox_result.get("verdict") == "FAIL":
        overall = "FAIL"
    elif discriminatory:
        overall = "PASS_WITH_OBSERVATIONS"
    elif tox_result.get("verdict") == "NOT_TESTED":
        overall = "NOT_TESTED"
    else:
        overall = "PASS"
    return {
        "engagement_id": engagement_id,
        "modality": modality,
        "sampling_strategy": inp.sampling_strategy,
        "sample_size": len(predictions_sample),
        "predictions_sample": predictions_sample,
        "toxicity_results": tox_result,
        "discriminatory_pattern_detected": discriminatory,
        "discriminatory_pattern_examples": examples,
        "overall_verdict": overall,
        "hitl_review_required": bool(discriminatory),
        "hitl_review_reason": (
            f"{len(flagged)} sampled predictions flagged for discriminatory "
            "patterns; HITL review required." if discriminatory else None),
        "sampling_narrative": sampling_narrative(
            len(predictions_sample), inp.sampling_strategy,
            str(tox_result.get("verdict", "NOT_TESTED")), skipped_reason),
        # Fix 47 (R15): an inspection for discriminatory patterns is the Art. 10 §2(f)
        # bias obligation, not Art. 15 §1 — and it is claimed only when it happened.
        "art10_2f_compliance_notes": art10_2f_note(
            len(predictions_sample), str(tox_result.get("verdict", "NOT_TESTED")), skipped_reason,
            text_outputs=outputs_are_text(inp, modality)),
        "generated_at": now,
    }
