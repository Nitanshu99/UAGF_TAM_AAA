"""Normalising the Verifier's issue list, and reading a material non-conformity out of it."""
from __future__ import annotations

from typing import Any

#: Issue keys the Verifier prompt defines and the runtime keeps.
_ISSUE_KEYS = ("severity", "field", "description", "recommendation",
               "materiality", "materiality_rationale", "issue_type", "articles")

#: What an issue is about. Only a defect in the artefact bears on its admission;
#: the other two are things the artefact accurately records about the provider,
#: and they reach the compliance matrix instead (T-20260914-015/016).
ARTEFACT_DEFECT = "artefact_defect"
PROVIDER_TYPES = frozenset({"evidence_gap", "provider_nonconformity"})
def issue_text(issue: Any) -> str:
    """Render one issue as the single line a text consumer needs.

    :param issue: A structured issue, or whatever the model emitted instead.
    :returns: The issue's description, or its string form.
    """
    if isinstance(issue, dict):
        return str(issue.get("description") or issue.get("issue")
                   or issue.get("field") or "")
    return str(issue or "")
def _normalise_issues(raw_issues: Any) -> list[dict[str, Any]]:
    """Coerce a model-emitted issue list into structured issue records.

    This flattened each issue to its ``description`` and dropped the rest (M12).
    ``PROMPT.md`` asks the Verifier for ``severity``, ``field``,
    ``recommendation``, ``materiality`` and ``materiality_rationale``, and
    insists the recommendation be actionable; none of it survived the parse.

    Two things were paying for that. ``build_rerun_context`` ships these issues
    into the rerun the Verifier ordered, so the agent was told what was wrong
    and never how to fix it — the mechanism is *verify, then re-run with
    feedback*, and it was carrying half the message. And
    ``verification.phase_outcome._blocking_issues`` filters this list for dicts
    with a blocking ``severity`` to build what the Orchestrator sees: against a
    list of strings it matched nothing, so ``blocking_issues`` was ``[]`` on all
    37 occurrences of the 2026-09-10 Mariposa run, including critiques carrying
    ``severity: critical``.

    :param raw_issues: The model's ``issues`` array, in any shape.
    :returns: One record per issue, each carrying at least ``description``.
    """
    if not isinstance(raw_issues, list):
        return []
    issues: list[dict[str, Any]] = []
    for item in raw_issues:
        if isinstance(item, dict):
            record = {k: item[k] for k in _ISSUE_KEYS if item.get(k)}
            record["description"] = issue_text(item)
            # Unknown or missing is a defect: the conservative reading keeps the gate.
            kind = str(item.get("issue_type") or "").strip().lower()
            record["issue_type"] = kind if kind in PROVIDER_TYPES else ARTEFACT_DEFECT
            if record["description"]:
                issues.append(record)
        elif item is not None and str(item):
            issues.append({"description": str(item), "issue_type": ARTEFACT_DEFECT})
    return issues
#: Verdicts that admit the artefact as evidence.
_ADMITTING = ("accept", "accept_with_notes")
def material_non_conformity(issues: list[dict[str, Any]]) -> dict[str, Any] | None:
    """The first issue the Verifier itself confirmed as material.

    :param issues: Normalised issue records.
    :returns: The blocking issue, or ``None``.
    """
    for issue in issues:
        if (isinstance(issue, dict) and str(issue.get("materiality", "")).lower() == "material"
                and is_defect(issue)):
            return issue
    return None


def is_defect(issue: Any) -> bool:
    """Whether *issue* is about the artefact itself (anything not typed as provider)."""
    return not (isinstance(issue, dict) and issue.get("issue_type") in PROVIDER_TYPES)


def rests_on_provider_issues(issues: list[dict[str, Any]], scores: dict | None) -> bool:
    """True when every blocking issue is about the provider and accuracy was not failed.

    :param issues: Normalised issue records.
    :param scores: The rubric scores; ``factual_accuracy`` 0 is a defect whatever the labels.
    """
    blocking = [i for i in issues if str(i.get("severity", "")).lower() in ("critical", "major")]
    return (bool(issues) and (scores or {}).get("factual_accuracy", 1) != 0
            and not any(is_defect(i) for i in blocking)
            and any(not is_defect(i) for i in issues))


__all__ = ["ARTEFACT_DEFECT", "PROVIDER_TYPES", "_ADMITTING", "_ISSUE_KEYS", "_normalise_issues",
           "is_defect", "issue_text", "material_non_conformity", "rests_on_provider_issues"]
