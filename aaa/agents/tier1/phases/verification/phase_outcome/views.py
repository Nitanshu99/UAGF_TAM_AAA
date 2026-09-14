"""Trimming a phase's report and critique down to what a sequencing decision turns on."""
from __future__ import annotations

from typing import Any

#: severities that should reach a sequencing decision; the rest are editorial.
_BLOCKING: tuple[str, ...] = ("critical", "major")

_MAX_ISSUES: int = 4
_SUMMARY_CHARS: int = 600
_ISSUE_CHARS: int = 300


def _trim(value: Any, limit: int) -> str:
    """Return *value* as a string clipped to *limit* characters.

    :param value: Any value to render into the envelope.
    :param limit: Maximum characters to keep.
    :returns: The clipped string (ellipsised when it was cut).
    """
    text = str(value or "")
    return text if len(text) <= limit else text[:limit] + "…"


def _blocking_issues(critique: dict[str, Any]) -> list[dict[str, str]]:
    """Return the critical/major issues of *critique*, trimmed and capped.

    :param critique: One stored ``verifier_critiques`` entry.
    :returns: At most :data:`_MAX_ISSUES` issues, each reduced to what an
        Orchestrator needs to decide whether to re-dispatch.
    """
    out: list[dict[str, str]] = []
    for issue in critique.get("issues") or []:
        if not isinstance(issue, dict):
            continue
        if str(issue.get("severity", "")).lower() not in _BLOCKING:
            continue
        out.append({
            "severity": str(issue.get("severity", "")),
            "field": str(issue.get("field", "")),
            "description": _trim(issue.get("description"), _ISSUE_CHARS),
            "recommendation": _trim(issue.get("recommendation"), _ISSUE_CHARS),
        })
        if len(out) == _MAX_ISSUES:
            break
    return out


__all__ = ["_blocking_issues", "_trim"]
