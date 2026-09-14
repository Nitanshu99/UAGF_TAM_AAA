"""The provider's declared performance figures, kept apart from the auditor's own.

T09 filled ``performance_metrics`` only from ``metric_suite``, so a model that
could not be scored produced an empty card, and case 06's seven declared ranking
metrics appeared nowhere in it (T-20260913-013). Model Cards (Mitchell et al.,
2019) report performance; assurance practice keeps the responsible party's
assertions separate from the practitioner's measurements. So declared figures
are recorded verbatim, labelled unverified, and every one that was not
independently recomputed is named in an observation with the reason.
"""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.model_validator.metrics import METRIC_MAP
from aaa.agents.tier2.model_validator.targets import TARGET_MAP
from aaa.tools.findings import make_finding

SOURCE = "stage_b.accuracy_metrics"


def declared_metrics(dossier: dict[str, Any]) -> dict[str, Any] | None:
    """The declared metrics block for T09, or ``None`` when nothing was declared.

    :param dossier: Stage B, or the T01b artefact carrying ``accuracy_metrics``.
    :returns: ``{source, verified: False, values}`` with the numeric values only.
    """
    values = {str(k): float(v) for k, v in (dossier.get("accuracy_metrics") or {}).items()
              if isinstance(v, (int, float)) and not isinstance(v, bool)}
    return {"source": SOURCE, "verified": False, "values": values} if values else None


def unverified_declared_finding(dossier: dict[str, Any], metrics_result: dict[str, Any],
                                access_mode: str | None) -> dict[str, Any] | None:
    """An observation naming each declared metric this phase did not recompute.

    :param dossier: Stage B or T01b.
    :param metrics_result: ``metric_suite`` output.
    :param access_mode: The declared ``model_access_mode``.
    :returns: The finding, or ``None`` when every declared metric was recomputed.
    """
    block = declared_metrics(dossier)
    if block is None:
        return None
    computed = metrics_result.get("metrics") or {}
    reasons = []
    for name in block["values"]:
        family = (METRIC_MAP.get(name) or TARGET_MAP.get(name) or (None,))[0]
        if computed.get(name) is not None:  # recomputed under its own name (ranking metrics)
            continue
        if family is None:
            reasons.append(f"{name} (no recomputation exists for this metric family)")
        elif not computed:
            reasons.append(f"{name} (no model predictions; model_access_mode="
                           f"{access_mode or 'not declared'})")
        elif computed.get(family) is None:
            reasons.append(f"{name} (not defined for this model's labels)")
    if not reasons:
        return None
    return make_finding(
        finding_id="P3-DECLARED-UNVERIFIED",
        description=("Declared performance metrics recorded but not independently "
                     "recomputed: " + "; ".join(reasons) + "."),
        materiality="observation", articles=["Art.15"], source_phase="P3",
        recommendation=("Provide model access or provider-logged predictions with ground "
                        "truth so the declared figures can be reproduced."))


__all__ = ["declared_metrics", "unverified_declared_finding"]
