"""Known-limitation derivation for the T09 model card.

Each limitation is a measurement or a missing input, stated as such. A primary
metric used to be flagged below a fixed 0.70 whatever the task or the provider's
own target, and an empty list read "No automated limitations detected." — a claim
no check established, beside case 05's 80-row evaluation of a CV screener, which
the Verifier escalated (T-20260913-099).
"""
from __future__ import annotations

import math
from statistics import NormalDist
from typing import Any

from aaa.agents.tier2.model_validator.targets import check_targets

#: The two-sided 95% normal quantile, derived rather than typed in.
_Z95 = NormalDist().inv_cdf(0.975)
#: What the automated checks look at, named when none of them raised anything.
_CHECKS = "metric computation, declared error-rate targets, provider robustness metrics"


def _sample_margin(n: Any) -> str | None:
    """The worst-case 95% margin of a rate measured on *n* rows (p = 0.5), in words."""
    if not isinstance(n, int) or isinstance(n, bool) or n <= 0:
        return None
    margin = _Z95 * math.sqrt(0.25 / n)
    return (f"Performance was measured on {n} evaluation rows; a rate measured on {n} rows "
            f"is known to within ±{margin:.1%} at 95% confidence at worst, so smaller "
            "differences between metrics or groups are not established.")


def _ranking_note(ranking: Any) -> str | None:
    """What ranking metrics rest on: queries, not rows, bound their precision."""
    if not isinstance(ranking, dict) or not ranking.get("computed"):
        return None
    return (f"Ranking metrics were recomputed over {ranking['n_queries']} queries "
            f"({ranking['n_rows']} ranked rows); their 95% intervals resample queries, so "
            "differences smaller than those intervals are not established.")


def derive_limitations(modality: str, metrics_result: dict[str, Any], t01b: dict[str, Any],
                       declared: dict[str, Any] | None = None,
                       reason: str | None = None) -> list[str]:
    """Derive the known limitations the audit measured or could not measure.

    :param modality: Normalised system modality.
    :param metrics_result: Output of ``metric_suite``.
    :param t01b: T01b Annex IV dossier artefact.
    :param declared: The declared metrics block (``{source, verified, values}``).
    :param reason: Why nothing was measured, when nothing was.
    :returns: Non-empty list of limitation statements.
    """
    limits: list[str] = []
    if metrics_result.get("primary_metric_value") is None:
        # "Rerun against a live evaluation set required" was written whatever the cause,
        # beside a supplied evaluation set and an absent model (case 06).
        limits.append(f"Performance was not measured: {reason or 'no metric could be computed'}."
                      + (" The declared metrics are reported unverified." if declared else ""))
    else:
        missed, _met = check_targets((declared or {}).get("values") or {},
                                     metrics_result.get("metrics") or {},
                                     metrics_result.get("confusion"))
        limits += [str(f.get("description")) for f in missed]
        limits += [m for m in [_ranking_note(metrics_result.get("ranking"))
                               or _sample_margin(metrics_result.get("evaluation_sample_size"))] if m]
    if modality == "cv":
        limits.append("Domain-shift sensitivity not characterised; see T11.")
    if not t01b.get("robustness_metrics"):
        limits.append("No provider-supplied robustness metrics; relying on Phase 3 probes.")
    return limits or [f"None of the automated checks ({_CHECKS}) raised a limitation; "
                      "that does not establish that the model has none."]
