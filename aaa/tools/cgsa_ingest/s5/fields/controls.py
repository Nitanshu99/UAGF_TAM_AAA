"""Per-control readers for the S5 dialect: ids, articles, gap text, evidence summary."""
from __future__ import annotations

from typing import Any


def controls_by_id(domains: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Index every scored control by id, across all domains."""
    return {c["control_id"]: c
            for d in (domains or []) for c in (d.get("controls") or [])
            if c.get("control_id")}


def articles_of(control: dict[str, Any]) -> list[str]:
    """**Every** EU AI Act article a control maps to.

    The contract's ``eu_ai_act_article`` is singular and the dialect's
    ``eu_ai_act_articles`` is not, and taking ``[0]`` to bridge them silently
    dropped the rest. On a real evaluated export **most controls name more than one
    article**, and many articles were reachable only as a *non-first* entry.

    The cost was a false PASS, which is the worst outcome this system can
    produce. A below-threshold monitoring-plan control names Articles 9 and 72;
    filed under Article 9 alone, **Art. 72 was admitted "with no findings
    raised"** on the 2026-09-10 MiniMax run. Two earlier runs hid it: their T15
    was rejected for unrelated reasons, so Art. 72 fell to INSUFFICIENT_EVIDENCE
    and the gap never showed.

    :param control: A CGSA control record.
    :returns: Article references, in the order the control lists them.
    """
    arts = [a for a in (control.get("eu_ai_act_articles") or []) if a]
    if arts:
        return arts
    single = control.get("eu_ai_act_article")
    return [single] if single else []


def article_of(control: dict[str, Any]) -> str | None:
    """The control's primary article — the contract's singular field."""
    arts = articles_of(control)
    return arts[0] if arts else None


def gap_text(control: dict[str, Any]) -> str | None:
    """The control's own account of its gap.

    The dialect writes it as ``gap_detail``; the contract calls the same field
    ``evidence_summary``. Both are the assessor's sentence about this control, so
    whichever is present is the finding text — there is nothing else to say.
    """
    return control.get("gap_detail") or control.get("evidence_summary")


def control_summary(control: dict[str, Any]) -> str | None:
    """The contract's ``evidence_summary`` for a control, gap or no gap.

    The dialect writes prose only where there is something wrong: a control that
    meets its threshold carries ``gap_detail: null``, which is why the
    *passing* controls were the last records
    to fail validation. Their outcome is still a fact the payload states, so it
    is stated here from the scores rather than left blank.
    """
    text = gap_text(control)
    if text:
        return text
    score, threshold = control.get("final_maturity_score"), control.get("threshold_score")
    if score is None or threshold is None:
        return None
    source = (control.get("evidence_metadata") or {}).get("source_document")
    return (f"Meets its threshold at maturity {score} of {threshold} required"
            + (f", assessed from {source}." if source else "."))
