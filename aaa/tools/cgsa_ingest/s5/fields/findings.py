"""Hand-off record completion for the S5 dialect: findings, constraints, low-confidence flags."""
from __future__ import annotations

from typing import Any

from aaa.tools.cgsa_ingest.s5.fields.controls import article_of, articles_of, gap_text


def actions_by_control(remediation: list[dict[str, Any]]) -> dict[str, str]:
    """Index the roadmap's remediation actions by the control they remediate."""
    return {r["control_id"]: r.get("action") or r.get("recommended_action") or ""
            for r in (remediation or []) if r.get("control_id")}


def finding_fields(entry: dict[str, Any], control: dict[str, Any],
                   actions: dict[str, str]) -> dict[str, Any]:
    """Fill a blocking finding's contract fields from its control record.

    The dialect's own ``description`` is a counter — "Hard constraint violated
    for control C02." repeated across 26 of 32 findings — so it is not used as
    the finding text where the control carries a real one.
    """
    filled = dict(entry)
    filled.setdefault("control_name", control.get("control_name"))
    text = gap_text(control) or entry.get("description")
    if text:
        filled.setdefault("finding", text)
    articles = articles_of(control)
    if articles:
        filled.setdefault("eu_ai_act_article", articles[0])
        # `articles_for` prefers the plural key, so every article the control
        # binds reaches the compliance matrix — not just the first.
        filled.setdefault("eu_ai_act_articles", articles)
    action = actions.get(entry.get("control_id", ""))
    if action:
        filled.setdefault("remediation_action", action)
    # The roadmap graded these controls critical/high/medium while T14's findings
    # read null: the grade is the control's own, and was never copied (T-20260914-057).
    if control.get("gap_severity"):
        filled.setdefault("gap_severity", control["gap_severity"])
    return filled


def constraint_fields(entry: dict[str, Any], control: dict[str, Any],
                      violated: bool) -> dict[str, Any]:
    """Fill a hard-constraint record's contract fields from its control record."""
    filled = dict(entry)
    filled.setdefault("control_name", control.get("control_name"))
    if entry.get("threshold") is not None:
        filled.setdefault("required_score", entry["threshold"])
    if entry.get("final_score") is not None:
        filled.setdefault("actual_score", entry["final_score"])
    article = article_of(control)
    if article:
        filled.setdefault("eu_ai_act_article", article)
    if violated:
        text = gap_text(control)
        if text:
            filled.setdefault("violation_description", text)
    return filled


def low_confidence_reason(entry: dict[str, Any]) -> str:
    """State why a control was flagged low-confidence, from what the dialect records.

    ``evidence_found`` separates the two cases the contract's ``flag_reason``
    exists to tell apart: a score with no document behind it at all, and one read
    from a document that did not say enough.
    """
    if entry.get("evidence_found") is False:
        return ("No supporting document was located for this control; the score "
                "rests on the self-assessment alone.")
    return (f"Supporting evidence was located but scored only "
            f"{entry.get('confidence')} confidence, so the maturity score is "
            f"inferred from limited documentation.")
