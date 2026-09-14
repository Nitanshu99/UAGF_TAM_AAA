"""T11 artefact update for the Tier-3 cyber audit."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from aaa.agents.tier3.cyber_agent.verdict import derive_verdict


def update_t11(t11: dict[str, Any], engagement_id: str, modality: str,
               probes: list[dict], injection: dict | None,
               extended: bool = True, probe_skipped: str = "",
               robustness: str | None = None,
               declared: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return T11 extended with the specialist probe outcomes.

    :param t11: The existing T11 payload (may be empty).
    :param engagement_id: Engagement identifier.
    :param modality: Verified modality.
    :param probes: Combined Phase 3 + specialist probes.
    :param injection: Injection-suite results (generative modalities only).
    :param extended: False when no Phase 3 T11 was available to extend — the
        notes then say so, rather than letting a report built from nothing read
        like an extension of one (P5).
    :param probe_skipped: Why the specialist adversarial probe measured nothing,
        if it did not run. Recorded in ``skipped_reason`` so an unmeasured probe
        is visible beside the verdict rather than only in its absence.
    :param robustness: The worse of Phase 3's and the specialist probe's verdicts.
    :param declared: The provider's ``robustness_metrics``.
    """
    new_t11 = dict(t11)
    # Required by the template. A spawn with no Phase 3 T11 has no clean pass of its
    # own to restate; unknown, not zero (T11@Cyber failed its schema on case 02).
    new_t11.setdefault("clean_accuracy", None)
    provenance = (
        "Independent security review performed per Falco 2021."
        if extended else
        "Independent security review performed per Falco 2021, but no Phase 3 "
        "T11 was available to extend: this report covers the specialist probes "
        "only and does not restate Phase 3's robustness evidence."
    )
    new_t11.update({
        "engagement_id": engagement_id,
        "modality": modality,
        "probes": probes,
        "overall_robustness_verdict": derive_verdict(probes, injection, robustness, declared),
        "art15_compliance_notes": (
            (t11.get("art15_compliance_notes") or "")
            + f"\n[Tier-3 Cyber Audit] {provenance}"
        ).strip(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    })
    if probe_skipped:
        new_t11["skipped_reason"] = (
            f"The Tier-3 specialist adversarial probe did not run: {probe_skipped}"
        )
    adv_accs = [p["adversarial_accuracy"] for p in probes
                if p.get("adversarial_accuracy") is not None]
    if adv_accs:
        new_t11["min_adversarial_accuracy"] = min(adv_accs)
    return new_t11


#: Robustness verdicts, least to most severe.
_SEVERITY = ("NOT_TESTED", "PASS", "PASS_WITH_OBSERVATIONS", "FAIL")


def worst_verdict(*verdicts: str | None) -> str | None:
    """The most severe of the measured verdicts, or ``None`` when none was given."""
    known = [v for v in verdicts if v in _SEVERITY]
    return max(known, key=_SEVERITY.index) if known else None


__all__ = ["update_t11", "worst_verdict"]
