"""Part 2 of the former ``robustness_probe`` module (auto-split)."""
from __future__ import annotations

from typing import Any, Callable, Sequence

from aaa.tools.robustness_probe.logger import _accuracy, _perturb, correct, logger


def _run_perturbation_probe(
    modality: str,
    predictor: Callable[[Any], Sequence[Any]],
    X: Any,
    y: list[Any],
    clean_acc: float,
    epsilon: float,
    categorical_features: Sequence[str] = (),
) -> dict[str, Any] | None:
    """Single perturbation probe — noise on numeric columns, flips on categoricals.

    :returns: The probe entry, or ``None`` when the probe could not be run.
        ``None`` rather than a zero-accuracy entry: a probe that raised has
        measured nothing, and reporting it as a total attack success would
        manufacture an Art. 15 failure out of a tooling error.
    """
    try:
        X_pert = _perturb(X, epsilon, modality, categorical_features)
        y_pred_pert = list(predictor(X_pert))
        adv_acc = _accuracy(y, y_pred_pert)
        flags = correct(y, y_pred_pert)
        success_rate = max(0.0, min(1.0, 1.0 - adv_acc / clean_acc)) if clean_acc > 0 else 0.0
        family = "feature_perturbation" if modality in {"tabular", "time_series"} else (
            "noise_injection" if modality == "cv"
            else "text_perturbation" if modality == "nlp" else "other"
        )
        flipped = modality != "nlp" and bool(categorical_features)
        kind = "char_noise" if modality == "nlp" else (
            "noise_and_category_flip" if flipped else "gaussian_noise")
        return {
            "probe_name": f"{kind}_eps_{epsilon}",
            "attack_family": family,
            "epsilon": float(epsilon),
            # Random noise has no norm bound; "l_inf" here read as a bounded adversarial
            # attack, and the Tier-3 narrative repeated it (case 01, 2026-09-14).
            "norm": None,
            "adversarial_accuracy": float(adv_acc),
            "attack_success_rate": float(success_rate),
            "accuracy_drop": float(max(0.0, clean_acc - adv_acc)),
            "tool": "char-noise" if modality == "nlp" else (
                "seeded-noise-and-category-flip" if flipped else "seeded-gaussian-noise"),
            "_correct": flags,  # per-row, for the verdict's intervals; stripped from T11
        }
    except Exception as exc:
        logger.info("Perturbation probe at eps=%s failed (%s); no result recorded.",
                    epsilon, exc)
        return None
