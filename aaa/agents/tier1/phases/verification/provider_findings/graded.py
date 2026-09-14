"""An artefact's own per-article grading bounds what a Verifier provider issue does to that article.

T15 grades Art. 12, 17 and 72 by fixed rules — a documented element, an element declared
absent, an element not evidenced. On case 01 it graded Art. 72 PASS_WITH_OBSERVATIONS
("not evidenced in the documents: data from deployers and affected persons"), and the
Verifier restated that element as a *material* provider non-conformity, failing Art. 72
(MiniMax run, 2026-09-14): an LLM's materiality label overriding the grading of the same
element. A Verifier that disagrees with a grading has found an artefact defect, which the
admission gate handles; carried as a provider issue, it is capped at the grading.
"""
from __future__ import annotations

from typing import Any, Callable

#: Templates that grade articles themselves: article → the block holding its status.
GRADED = {"T15_monitoring_logging_review": {"Art.12": "art12_record_keeping",
                                            "Art.17": "art17_qms",
                                            "Art.72": "art72_post_market_plan"}}

Load = Callable[[str], Any]


def graded_statuses(tid: str, state: dict[str, Any], load: Load | None) -> dict[str, str]:
    """``{article: status}`` as *tid*'s stored artefact graded them; empty when unknown."""
    fields = GRADED.get(tid)
    ref = (state.get("phase_artefacts") or {}).get(tid)
    uri = ref.get("uri") if isinstance(ref, dict) else None
    content = load(uri) if fields and uri and load else None
    if not isinstance(content, dict) or not fields:
        return {}
    return {article: str(content[field]["status"]) for article, field in fields.items()
            if isinstance(content.get(field), dict) and content[field].get("status")}


def capped(issue: dict[str, Any], articles: list[str], statuses: dict[str, str]) -> dict[str, Any]:
    """*issue*, possibly material when every article it reaches was graded short of FAIL."""
    graded = [statuses.get(a) for a in articles]
    if (str(issue.get("materiality")).lower() != "material" or not articles
            or None in graded or "FAIL" in graded):
        return issue
    return {**issue, "materiality": "possibly_material", "description": (
        f"{issue.get('description')} Carried as possibly material: the artefact graded "
        f"{', '.join(f'{a} {s}' for a, s in zip(articles, graded))}, and a disagreement with that "
        "grading is an artefact defect for review, not a change of verdict.")}


__all__ = ["GRADED", "capped", "graded_statuses"]
