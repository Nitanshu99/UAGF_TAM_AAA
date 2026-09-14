"""Whether a perturbation measurably degrades the model, and whether a declared figure holds.

The verdict was a fixed floor on adversarial accuracy (PASS >= 0.70, FAIL < 0.50),
blind to the clean accuracy, the sample size and what the provider declared
(T-20260914-007). A drop is *established* when the paired bootstrap interval of the
accuracy lost on the same rows excludes zero; a declared
``adversarial_accuracy_<kind>_<level>`` is judged against the interval of the probe
that measures exactly that kind at that level.
"""
from __future__ import annotations

import re
from typing import Any, Sequence

from aaa.tools.metric_suite.interval import LEVEL, ROUNDS, SEED

_DECLARED = re.compile(r"^adversarial_accuracy_([a-z_]+?)_(\d+(?:_\d+)?)$")
#: The perturbations the probe itself performs. A declared figure under any other kind
#: (an ``l_inf`` gradient attack, say) is not something these probes can re-measure.
PROBE_KINDS = frozenset({"gaussian_noise", "noise_and_category_flip", "char_noise"})


def _percentiles(values: Any) -> tuple[float, float]:
    import numpy as np  # type: ignore

    tail = (1 - LEVEL) / 2 * 100
    return float(np.percentile(values, tail)), float(np.percentile(values, 100 - tail))


def intervals(clean: Sequence[bool], perturbed: Sequence[bool]) -> dict[str, tuple[float, float]]:
    """95% intervals of the perturbed accuracy and of the paired drop, on the same rows."""
    import numpy as np  # type: ignore

    c, p = np.asarray(clean, dtype=float), np.asarray(perturbed, dtype=float)
    idx = np.random.default_rng(SEED).integers(0, len(c), size=(ROUNDS, len(c)))
    return {"accuracy": _percentiles(p[idx].mean(axis=1)),
            "drop": _percentiles((c[idx] - p[idx]).mean(axis=1))}


def declared_levels(declared: dict[str, Any] | None) -> dict[tuple[str, float], float]:
    """``{(probe kind, level): declared accuracy}`` from ``robustness_metrics`` keys."""
    out: dict[tuple[str, float], float] = {}
    for key, value in (declared or {}).items():
        match = _DECLARED.match(str(key))
        if (match and match.group(1) in PROBE_KINDS
                and isinstance(value, (int, float)) and not isinstance(value, bool)):
            out[(match.group(1), float(match.group(2).replace("_", ".", 1)))] = float(value)
    return out


def probe_kind(probe: dict[str, Any]) -> tuple[str, float]:
    """``(kind, level)`` of a probe entry, as its name and epsilon record them."""
    name = str(probe.get("probe_name", ""))
    return name.split("_eps_", maxsplit=1)[0], float(probe.get("epsilon") or 0.0)


__all__ = ["PROBE_KINDS", "declared_levels", "intervals", "probe_kind"]
