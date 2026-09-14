"""Part 4 of the former ``robustness_probe`` module (auto-split)."""
from __future__ import annotations

from typing import Any, Callable, Sequence

from aaa.tools.robustness_probe.degradation import declared_levels
from aaa.tools.robustness_probe.logger import _DEFAULT_EPSILONS
from aaa.tools.robustness_probe.run_perturbation_probe import _run_perturbation_probe
from aaa.tools.robustness_probe.sample import prepare_sample
from aaa.tools.robustness_probe.unmeasured import unmeasured_notes
from aaa.tools.robustness_probe.verdict import decide


def robustness_probe(
    model: Any = None,
    X: Any = None,
    y_true: Sequence[Any] | None = None,
    modality: str = "tabular",
    epsilons: Sequence[float] | None = None,
    predict_fn: Callable[[Any], Sequence[Any]] | None = None,
    sample_size: int | None = None,
    categorical_features: Sequence[str] | None = None,
    declared: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Run a battery of adversarial / perturbation probes.

    Parameters
    ----------
    model:
        Trained model.  Used both as the foolbox/textattack target and
        (if ``predict_fn`` is ``None``) as the source of ``predict``.
    X:
        Feature matrix or text inputs.
    y_true:
        Ground-truth labels — required to compute attack success.
    modality:
        ``tabular`` / ``cv`` / ``nlp`` / ``llm`` / ``time_series``.
    epsilons:
        Perturbation scales: the noise standard deviation as a fraction of each numeric
        feature's own, and the share of categorical cells flipped (not an ``L_inf`` bound).
    predict_fn:
        Callable ``X → y_pred``.  Falls back to ``model.predict``.
    sample_size:
        Maximum rows used by the probe; every evaluation row by default. A fixed 200-row
        cap probed 200 of case 01's 300 rows and widened every interval for nothing.
    categorical_features:
        Columns of ``X`` that are label-encoded categories.  They are
        perturbed by category flip rather than by Gaussian noise, which on an
        identifier column measures nothing.

    declared:
        The provider's ``robustness_metrics``; a declared
        ``adversarial_accuracy_<kind>_<level>`` is probed at its own level and judged.

    Returns
    -------
    dict with ``clean_accuracy``, ``probes`` list,
    ``overall_robustness_verdict``, and ``min_adversarial_accuracy``.
    """
    levels = {*(epsilons or _DEFAULT_EPSILONS), *(lvl for _k, lvl in declared_levels(declared))}
    prepared = prepare_sample(X, y_true, model, predict_fn, sample_size, modality)
    if "probes" in prepared:
        return prepared
    n, y, X_sample, predictor, clean_acc = prepared["sample"]

    categorical = list(categorical_features or ())
    attempted = [_run_perturbation_probe(modality, predictor, X_sample, y, clean_acc, eps,
                                         categorical)
                 for eps in sorted(levels)]
    probes = [p for p in attempted if p is not None]
    verdict, notes = decide(probes, prepared["clean"], declared)
    for probe in probes:
        probe.pop("_correct", None)

    adv_accs = [p["adversarial_accuracy"] for p in probes if p["adversarial_accuracy"] is not None]
    result: dict[str, Any] = {
        "clean_accuracy": clean_acc,
        "evaluation_sample_size": n,
        "probes": probes,
        "overall_robustness_verdict": verdict,
        "min_adversarial_accuracy": min(adv_accs) if adv_accs else None,
        "degradation_notes": notes + unmeasured_notes(declared),
    }
    if len(probes) < len(attempted):
        result["skipped_reason"] = (
            f"{len(attempted) - len(probes)} of {len(attempted)} perturbation probes "
            "could not be executed; the verdict rests on the remainder.")
    return result
