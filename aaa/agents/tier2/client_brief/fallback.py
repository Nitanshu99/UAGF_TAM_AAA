"""Deterministic sections for when the model does not answer for an article.

These read worse than the written ones, and they say so. What they will not do
is invent: every line is a field copied out of the evidence bundle, so a
fallback section is thinner than a written one but never less true.
"""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.client_brief.constants import verdict_label


def _declared_claims(bundle: dict[str, Any]) -> list[str]:
    """Restate only the claims this article's evidence actually bears on.

    Reprinting the whole intake declaration under all seventeen requirements
    buries the one line that matters, so the deterministic path reports the
    declarations the audit recorded a mismatch against, and the ones a finding
    named for itself.
    """
    decl = bundle["provider_declaration"]
    declared = decl["declared_by_provider"]
    out = [f"You declared `{field}` as `{declared.get(field)}`; the audit's check "
           f"of that declaration came back `{result}`."
           for field, result in decl["audit_check_of_each_declaration"].items()
           if result != "match"]
    out += [f"On this requirement you stated: {f['declared']}"
            for f in bundle["findings"] if f.get("declared")]
    return out


def _evidence_lines(bundle: dict[str, Any]) -> list[str]:
    """State what the audit found, from findings and rejected artefacts."""
    lines = [f["description"] + (f" The audit observed: {f['observed']}"
                                 if f.get("observed") else "")
             for f in bundle["findings"]]
    lines += [f"`{r['template_id']}` was not admitted as evidence by the "
              f"independent reviewer: {r['reason']}"
              for r in bundle["rejected_artefacts"]]
    lines += [f"Governance control `{c['control_id']}` "
              f"({c.get('control_name', '')}): {c.get('finding', '')}"
              for c in bundle["governance_controls"]]
    return lines or ["No finding was raised against this requirement."]


def _actions(bundle: dict[str, Any]) -> list[str]:
    """Collect the remediation already recorded against this article."""
    actions = [f["recommendation"] for f in bundle["findings"] if f.get("recommendation")]
    actions += [c["remediation_action"] for c in bundle["governance_controls"]
                if c.get("remediation_action")]
    return list(dict.fromkeys(actions))


def deterministic_section(bundle: dict[str, Any]) -> dict[str, Any]:
    """Build one article's section from the bundle alone, with no LLM call.

    :param bundle: The article's evidence bundle from :mod:`.bundle`.
    :returns: A section in the same shape as a written one, flagged
        ``llm_written: False`` so the brief can say which sections these are.
    """
    verdict = bundle["verdict"]
    return {
        "article": bundle["article"],
        "subject": bundle["subject"],
        "verdict": verdict,
        "headline": f"{bundle['subject']} — {verdict_label(str(verdict)).lower()}.",
        "what_you_told_us": _declared_claims(bundle),
        "what_the_evidence_shows": _evidence_lines(bundle),
        "why_this_verdict": bundle.get("audit_rationale"),
        "what_to_do": _actions(bundle),
        "llm_written": False,
    }
