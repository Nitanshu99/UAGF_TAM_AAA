"""What one Verifier provider issue becomes: a finding, and for a material gap a record."""
from __future__ import annotations

from typing import Any

from aaa.tools.findings import make_finding

_DEFAULT_ACTION = {
    "evidence_gap": "Supply the documentation or evidence the requirement needs.",
    "provider_nonconformity": "Bring the system or its documentation into line with the "
                              "requirement, or correct the declaration.",
}


def carried(issue: dict[str, Any]) -> bool:
    """Whether an issue about the provider is material enough to reach the matrix."""
    return (issue.get("issue_type") in _DEFAULT_ACTION
            and str(issue.get("materiality", "")).lower() in ("material", "possibly_material"))


def finding(issue: dict[str, Any], finding_id: str, tid: str, articles: list[str],
            phase_id: str) -> dict[str, Any]:
    """The finding for one provider issue on *tid*.

    A material non-conformity keeps its materiality, so it fails its articles; a gap is
    at most possibly material here, because what a material gap does to an article is
    INSUFFICIENT_EVIDENCE, recorded beside it (:func:`gap_record`), not FAIL.
    """
    kind = str(issue["issue_type"])
    material = str(issue.get("materiality")).lower() == "material"
    words = "evidence gap" if kind == "evidence_gap" else "provider non-conformity"
    return make_finding(
        finding_id=finding_id,
        description=f"Verifier on {tid} ({words}): {issue.get('description')}",
        materiality="material" if material and kind != "evidence_gap" else "possibly_material",
        articles=articles, source_phase=phase_id,
        recommendation=str(issue.get("recommendation") or _DEFAULT_ACTION[kind]))


def gap_record(issue: dict[str, Any], tid: str, articles: list[str], *,
               phase_id: str, phase_label: str) -> dict[str, Any] | None:
    """The insufficiency a *material* evidence gap holds on its articles, else ``None``."""
    if issue.get("issue_type") != "evidence_gap" or str(issue.get("materiality")).lower() != "material":
        return None
    return {"phase_id": phase_id, "phase_label": phase_label, "template_id": tid,
            "articles": list(articles), "reason": str(issue.get("description") or "")[:400]}


__all__ = ["carried", "finding", "gap_record"]
