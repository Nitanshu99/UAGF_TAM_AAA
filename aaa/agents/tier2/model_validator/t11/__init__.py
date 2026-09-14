"""T11 robustness report builder."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.model_validator.t11.narrative import build_narrative, noise_summary
from aaa.tools.robustness_probe.unmeasured import THREAT_MODEL


def build_t11(engagement_id: str, modality: str,
              robustness_result: dict[str, Any], now: str) -> dict[str, Any]:
    """Build the T11 robustness report.

    :param engagement_id: Engagement identifier.
    :param modality: Normalised system modality.
    :param robustness_result: Output of ``robustness_probe``.
    :param now: ISO-8601 generation timestamp.
    :returns: T11 robustness-report dictionary.
    """
    verdict = robustness_result.get("overall_robustness_verdict", "NOT_TESTED")
    return {
        "engagement_id": engagement_id,
        "modality": modality,
        "clean_accuracy": robustness_result.get("clean_accuracy"),
        "evaluation_sample_size": robustness_result.get("evaluation_sample_size"),
        "probes": robustness_result.get("probes", []),
        "noise_robustness": noise_summary(robustness_result.get("probes") or []),
        "overall_robustness_verdict": verdict,
        "min_adversarial_accuracy": robustness_result.get("min_adversarial_accuracy"),
        "robustness_narrative": build_narrative(modality, robustness_result),
        "skipped_reason": robustness_result.get("skipped_reason"),
        "art15_compliance_notes": art15_note(robustness_result, verdict),
        "generated_at": now,
    }


def art15_note(result: dict[str, Any], verdict: str) -> str:
    """The Art. 15 note, never claiming probes ran when none did (T-20260913-086)."""
    if verdict == "NOT_TESTED":
        return (f"Robustness probes were not executed: {result.get('skipped_reason') or 'no probe ran'}. "
                "This report provides no Art. 15 robustness evidence.")
    return (f"Robustness probes executed per Art. 15. Verdict: {verdict} — FAIL where a declared "
            f"robustness figure lies above the probe's 95% interval, PASS_WITH_OBSERVATIONS "
            f"where a probe's accuracy drop on the same rows is established, PASS otherwise. "
            f"{THREAT_MODEL}")


__all__ = ["art15_note", "build_narrative", "build_t11", "noise_summary"]
