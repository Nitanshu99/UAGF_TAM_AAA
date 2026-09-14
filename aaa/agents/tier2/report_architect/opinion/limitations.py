"""The scope limitations an opinion discloses (ISA 705: a limitation is stated, not implied)."""
from __future__ import annotations

from typing import Any


def scope_limitation_text(limitations: list[dict[str, Any]] | None) -> str:
    """One sentence per kind of limitation, or ``""`` when every procedure was performed.

    :param limitations: ``scope_limitations`` from :func:`apply_audit_programme`.
    """
    if not limitations:
        return ""
    def item(x: dict[str, Any]) -> str:
        return f"{x['title']} ({x['article']}: {x.get('reason') or 'reason not recorded'})"
    removed = [item(x) for x in limitations if x.get("effect") == "article_unevidenced"]
    disclosed = [item(x) for x in limitations if x.get("effect") != "article_unevidenced"]
    parts = []
    if removed:
        parts.append("Procedures of the audit programme that could not be performed, leaving "
                     "their article without sufficient evidence: " + "; ".join(removed) + ".")
    if disclosed:
        parts.append("Supplementary procedures not performed, disclosed as scope limitations "
                     "without changing a conclusion: " + "; ".join(disclosed) + ".")
    return " ".join(parts)


__all__ = ["scope_limitation_text"]
