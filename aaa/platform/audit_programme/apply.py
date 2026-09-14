"""Turning procedure outcomes into scope limitations and, where required, unevidenced articles."""
from __future__ import annotations

import logging
from typing import Any

from aaa.platform.audit_programme.procedures import PERFORMED, PROGRAMME

logger = logging.getLogger(__name__)


def _limitation(procedure_id: str, record: dict[str, Any], unevidenced: bool) -> dict[str, Any]:
    proc = PROGRAMME[procedure_id]
    return {"procedure": procedure_id, "title": proc.title, "phase": proc.phase,
            "article": proc.article, "element": proc.element, "sufficient": proc.sufficient,
            "reason": record.get("reason"),
            "effect": "article_unevidenced" if unevidenced else "disclosed"}


def apply_audit_programme(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Record every procedure not performed; unevidence an element nothing sufficient covered.

    An element whose sufficient procedures all have outcomes and none was performed
    leaves its article INSUFFICIENT_EVIDENCE. A supplementary procedure not performed
    changes no verdict: it is disclosed. Idempotent — safe to call on every derivation.

    :param state: The mutable AuditState; ``procedure_outcomes`` is read,
        ``scope_limitations`` and ``insufficient_evidence_articles`` are written.
    :returns: The scope limitations, in programme order.
    """
    outcomes = {k: v for k, v in (state.get("procedure_outcomes") or {}).items()
                if k in PROGRAMME and isinstance(v, dict)}
    elements: dict[tuple[str, str], list[str]] = {}
    for procedure_id in outcomes:
        proc = PROGRAMME[procedure_id]
        elements.setdefault((proc.article, proc.element), []).append(procedure_id)
    limitations: list[dict[str, Any]] = []
    recorded: list[str] = state.setdefault("insufficient_evidence_articles", [])
    for (article, _element), ids in elements.items():
        sufficient = [i for i in ids if PROGRAMME[i].sufficient]
        unevidenced = bool(sufficient) and all(outcomes[i]["outcome"] != PERFORMED for i in sufficient)
        if unevidenced and article not in recorded:
            recorded.append(article)
        limitations += [_limitation(i, outcomes[i], unevidenced and PROGRAMME[i].sufficient)
                        for i in ids if outcomes[i]["outcome"] != PERFORMED]
    order = list(PROGRAMME)
    state["scope_limitations"] = sorted(limitations, key=lambda x: order.index(x["procedure"]))
    if limitations:
        logger.warning("Audit programme: %d procedure(s) not performed: %s", len(limitations),
                       ", ".join(f"{x['procedure']} ({x['effect']})" for x in limitations))
    return state["scope_limitations"]


__all__ = ["apply_audit_programme"]
