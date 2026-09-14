"""The measurements themselves, not the addresses they live at — finding Q13.

"Explainability & fairness (Art. 13)" and "Security & robustness (Art. 15)"
rendered seven ``minio://`` URIs and nothing else, in a report whose reader
cannot resolve a ``minio://`` URI.  The run behind Q13 had produced ranked SHAP
importances, five LIME explanations and a three-point robustness curve; none of
it appeared.

So the sections resolve their artefacts and render what is in them.  The URI
stays, demoted to what it always was — provenance for the number above it,
rather than a substitute for it.
"""
from __future__ import annotations

import logging
from typing import Any

from aaa.tools.report_render.numbers import fmt
from aaa.tools.report_render.pdf.fairness_rows import fairness_rows
from aaa.tools.report_render.pdf.robustness_rows import robustness_rows

logger = logging.getLogger(__name__)

#: How many ranked features are worth a reader's attention on one page.
TOP_FEATURES = 6


def resolve(state: dict[str, Any], store: Any, tid: str) -> dict[str, Any]:
    """Fetch one phase artefact's payload, fail-soft.

    :param state: Audit state carrying ``phase_artefacts``.
    :param store: Evidence store; ``None`` resolves nothing.
    :param tid: Template id to fetch.
    :returns: The payload, or ``{}`` when it cannot be resolved.
    """
    ref = (state.get("phase_artefacts") or {}).get(tid) or {}
    uri = ref.get("uri") if isinstance(ref, dict) else None
    if not uri or store is None:
        return {}
    try:
        return store.get_artefact(uri) or {}
    except Exception as exc:  # noqa: BLE001 — evidence rendering is best-effort
        logger.warning("report evidence %s unresolvable: %s", tid, exc)
        return {}


def explainability_rows(t10: dict[str, Any]) -> list[tuple[str, str]]:
    """Ranked global attributions and the local-explanation count from T10."""
    if not t10:
        return []
    glob = t10.get("global_explanation") or {}
    ranked = (glob.get("feature_importance") or glob.get("feature_importances") or [])
    rows: list[tuple[str, str]] = [
        ("Techniques applied", ", ".join(t10.get("techniques_applied") or []) or "—"),
        ("Attribution method", str(glob.get("technique") or "—")),
    ]
    for item in ranked[:TOP_FEATURES]:
        rows.append((f"  {item.get('rank', '')}. {item.get('feature', '')}",
                     fmt(item.get("importance"))))
    local = t10.get("local_explanations") or []
    rows.append(("Local explanations", f"{len(local)} instance(s) explained"))
    if t10.get("skipped_reason"):
        rows.append(("Degraded", str(t10["skipped_reason"])))
    return rows










__all__ = ["TOP_FEATURES", "explainability_rows", "fairness_rows", "resolve",
           "robustness_rows"]
