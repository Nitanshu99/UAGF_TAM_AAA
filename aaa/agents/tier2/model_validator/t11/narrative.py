"""The T11 narrative and noise summary: what the probes measured, in words."""
from __future__ import annotations

from typing import Any

#: Probe kinds that perturb inputs with random noise, as ``run_perturbation_probe`` names them.
_NOISE_KINDS = ("gaussian_noise", "noise_and_category_flip", "char_noise")


def noise_summary(probes: list[dict[str, Any]]) -> dict[str, Any] | None:
    """The non-adversarial noise result, at the most severe level the probe tested.

    The field was hardcoded ``None`` while the probe measured it for every case with
    a scorable model (T-20260913-038). The largest tested epsilon is reported: one
    summary of robustness to noise should be the conservative one.

    :param probes: T11 probe entries.
    :returns: ``{noise_type, noise_level, accuracy_under_noise}``, or ``None`` when no
        noise probe ran.
    """
    noisy = [p for p in probes if str(p.get("probe_name", "")).startswith(_NOISE_KINDS)]
    if not noisy:
        return None
    worst = max(noisy, key=lambda p: float(p.get("epsilon") or 0.0))
    kind = next(k for k in _NOISE_KINDS if str(worst["probe_name"]).startswith(k))
    return {"noise_type": kind, "noise_level": worst.get("epsilon"),
            "accuracy_under_noise": worst.get("adversarial_accuracy")}


def build_narrative(modality: str, result: dict[str, Any]) -> str:
    """Compose a free-text robustness narrative for T11.

    :param modality: Normalised system modality.
    :param result: Output of ``robustness_probe``.
    :returns: Narrative paragraph for T11.
    """
    verdict = result.get("overall_robustness_verdict", "NOT_TESTED")
    if verdict == "NOT_TESTED":
        return (f"Robustness probes were not executed for {modality} modality "
                f"({result.get('skipped_reason') or 'no model/data available'}).")
    clean = result.get("clean_accuracy")
    min_adv = result.get("min_adversarial_accuracy")
    n_probes = len(result.get("probes", []))
    head = f"{modality} robustness verdict: {verdict}. "
    if isinstance(clean, float):
        head += f"Clean accuracy: {clean:.3f}. "
    tail = (f"Lowest accuracy under perturbation: {min_adv:.3f} across {n_probes} probes."
            if isinstance(min_adv, float) else
            f"Adversarial accuracy could not be measured across {n_probes} probes.")
    notes = " ".join(result.get("degradation_notes") or [])
    return head + tail + (f" {notes}" if notes else " No probe established an accuracy drop.")


__all__ = ["build_narrative", "noise_summary"]
