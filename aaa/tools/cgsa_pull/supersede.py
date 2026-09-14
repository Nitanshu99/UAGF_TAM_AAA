"""The evaluated export that supersedes a declared self-assessment of the same system.

Two dialects of one assessment can be on file. The wizard finds its client's by name,
and :func:`~aaa.tools.cgsa_pull.narrow._narrow` lets the evaluated export supersede
a self-assessment of the same system, because only it carries the thresholds a
control-level non-conformity is derived from. The CLI and API pulled whatever id the
dossier declared instead, so case 06 was audited against the self-assessment on one
entry point and the evaluated export on the other, and six articles differed
(2026-09-14, T-20260914-062). Every entry point now applies the same rule.
"""
from __future__ import annotations

from typing import Any

from aaa.tools.cgsa_pull.compat import is_evaluated
from aaa.tools.cgsa_pull.discover import discover_assessments
from aaa.tools.cgsa_pull.tokens import _org_tokens, _system_tokens


def _same_system(declared: frozenset[str], candidate: str) -> bool:
    """Whether two system names name one system — one's tokens contain the other's."""
    other = _system_tokens(candidate)
    return bool(declared) and bool(other) and (declared <= other or other <= declared)


def evaluated_counterpart(payload: Any, roots: list[str] | None = None) -> str | None:
    """The one evaluated export filed for the organisation and system *payload* describes.

    :param payload: The declared assessment, as pulled.
    :param roots: Directories to search; defaults to the configured fixture roots.
    :returns: Its assessment id, or ``None`` when *payload* is itself evaluated, names
        no organisation, or zero or several evaluated exports match.
    """
    if not isinstance(payload, dict) or is_evaluated(payload):
        return None
    raw = payload.get("metadata")
    meta: dict[str, Any] = raw if isinstance(raw, dict) else {}
    organisation = _org_tokens(str(meta.get("organisation_name") or ""))
    system = _system_tokens(str(meta.get("system_under_audit") or ""))
    if not organisation:
        return None
    matches = [a["assessment_id"] for a in discover_assessments(roots)
               if a["evaluated"] and _org_tokens(a["organisation_name"]) == organisation
               and _same_system(system, a["system_under_audit"])]
    return matches[0] if len(matches) == 1 else None


__all__ = ["evaluated_counterpart"]
