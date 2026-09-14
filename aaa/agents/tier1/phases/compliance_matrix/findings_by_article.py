"""Part 3 of the former ``compliance_matrix`` module (auto-split)."""
from __future__ import annotations

from aaa.agents.tier1.phases.compliance_matrix.collect_admitted_articles import (  # noqa: F401
    _collect_admitted_articles,
)
from aaa.agents.tier1.phases.compliance_matrix.logger import (  # noqa: F401
    _ADMITTED_VERDICTS,
    _CORE_HIGH_RISK_ARTICLES,
    _TEMPLATE_ARTICLES,
    _core_article,
    logger,
)
from aaa.tools.findings import articles_for


def _findings_by_article(state: dict) -> dict[str, list[dict]]:
    """Index blocking findings (phase + CGSA) by the articles they map to."""
    index: dict[str, list[dict]] = {}
    sources = list(state.get("blocking_findings", []) or [])
    for f in state.get("cgsa_blocking_findings", []) or []:
        # The CGSA schema forbids `gap_severity` on a blocking finding — its
        # items allow only control_id, control_name, eu_ai_act_article, finding
        # and remediation_action — so reading one downgraded *every* governance
        # gap to `possibly_material` by construction, and no article could ever
        # reach FAIL from a self-assessment declaring itself non-compliant.
        # Membership of `blocking_findings` is itself the severity signal; an
        # explicit severity, where a payload carries one, still wins.
        sev = str(f.get("gap_severity", "")).lower()
        materiality = "possibly_material" if sev in {"low", "medium"} else "material"
        sources.append({**f, "materiality": f.get("materiality", materiality)})
    for f in sources:
        for art in articles_for(f):
            index.setdefault(art, []).append(f)
            base = _core_article(art)
            if base != art:
                index.setdefault(base, []).append(f)
    return index


def _cgsa_controls_for(state: dict, article: str) -> list[str]:
    """Return CGSA control ids mapped to an article, if the payload provides them."""
    payload = state.get("cgsa_payload") or {}
    matrix = payload.get("eu_ai_act_compliance_matrix") or {}
    base = _core_article(article)
    key = "article_" + base.replace("Art.", "").strip()
    entry = matrix.get(key) or {}
    return list(entry.get("controls_mapped", []) or [])
