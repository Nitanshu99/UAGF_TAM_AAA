"""The four per-section translations :func:`~aaa.tools.cgsa_ingest.s5.dialect.adapt_s5_dialect` applies.

Each completes one section of the S5 dialect in place from data the payload
already carries: control evidence summaries, hand-off findings, hard-constraint
records and the article matrix's control-id lists.
"""
from __future__ import annotations

from typing import Any

from aaa.tools.cgsa_ingest.s5.fields import (
    article_control_ids,
    constraint_fields,
    control_summary,
    finding_fields,
    low_confidence_reason,
    positive_findings,
)


def adapt_controls(domains: list[dict[str, Any]]) -> None:
    """Give each control the ``evidence_summary`` the contract requires."""
    for domain in domains or []:
        for control in domain.get("controls") or []:
            text = control_summary(control)
            if text:
                control.setdefault("evidence_summary", text)


def adapt_handoff(handoff: dict[str, Any], controls: dict[str, dict[str, Any]],
                   actions: dict[str, str]) -> None:
    """Complete the hand-off's findings and low-confidence records."""
    handoff["blocking_findings"] = [
        finding_fields(entry, controls.get(entry.get("control_id", ""), {}), actions)
        for entry in (handoff.get("blocking_findings") or [])]
    handoff["low_confidence_controls"] = [
        {**entry, "flag_reason": entry.get("flag_reason") or low_confidence_reason(entry)}
        for entry in (handoff.get("low_confidence_controls") or [])]
    if not handoff.get("positive_findings"):
        handoff["positive_findings"] = positive_findings(controls)


def adapt_constraints(results: dict[str, Any],
                       controls: dict[str, dict[str, Any]]) -> None:
    """Complete both hard-constraint lists from their control records."""
    for key, violated in (("violated_constraints", True),
                          ("satisfied_constraints", False)):
        results[key] = [
            constraint_fields(entry, controls.get(entry.get("control_id", ""), {}), violated)
            for entry in (results.get(key) or [])]


def adapt_matrix(matrix: dict[str, Any]) -> None:
    """Restore the mapped / satisfied control-id lists from the counts."""
    for entry in matrix.values():
        if not isinstance(entry, dict):
            continue
        mapped, satisfied = article_control_ids(entry)
        if isinstance(entry.get("controls_mapped"), int):
            entry["controls_mapped"] = mapped
        if isinstance(entry.get("controls_satisfied"), int):
            entry["controls_satisfied"] = satisfied
