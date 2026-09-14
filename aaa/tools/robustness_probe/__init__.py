"""robustness_probe — Adversarial robustness probes (§4.2).

Returns a structured dict compatible with the T11_robustness_report
``probes`` array.

Production paths:
    - CV / tabular:  ``foolbox`` (FGSM / PGD / DeepFool)
    - NLP:           ``textattack`` (TextFooler / PWWS)
Fallback: feature-perturbation probe — Gaussian noise added to
                  numeric features, attack success measured against
                  user-provided ``y_true`` and ``predict_fn``.

Usage
-----
    from src.tools.robustness_probe import robustness_probe

    result = robustness_probe(
        model=clf,
        X=X_test,
        y_true=y_test,
        modality="tabular",
        epsilons=[0.05, 0.1, 0.2],
    )"""
from aaa.tools.robustness_probe.categorical_perturb import flip_categoricals  # noqa: F401
from aaa.tools.robustness_probe.core import robustness_probe  # noqa: F401
from aaa.tools.robustness_probe.logger import (  # noqa: F401
    _DEFAULT_EPSILONS,
    _accuracy,
    _perturb,
    logger,
)
from aaa.tools.robustness_probe.run_perturbation_probe import _run_perturbation_probe  # noqa: F401
from aaa.tools.robustness_probe.verdict import _empty_result, decide  # noqa: F401

__all__ = [
    'logger',
    '_DEFAULT_EPSILONS',
    '_perturb',
    'flip_categoricals',
    '_accuracy',
    '_run_perturbation_probe',
    'decide',
    '_empty_result',
    'robustness_probe',
]
