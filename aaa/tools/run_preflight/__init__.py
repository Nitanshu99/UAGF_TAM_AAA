"""Check a run against its reference *before* dispatching it.

A paid run that is not comparable with the reference is worse than no run: its
differences read as findings. On 2026-09-11 a Mariposa run was dispatched
against a self-assessment CGSA export where the reference had used the evaluated
S5 one. Six article verdicts softened — Arts. 5, 11 and 14 from FAIL to PASS,
Arts. 12, 50 and 72 from FAIL to INSUFFICIENT_EVIDENCE — and nothing logged a
word about it. The case document's own header said so in advance: *"CGSA the
real S5 export of 2026-09-03, not the mock fixture"*.

Run it before spending anything::

    python -m aaa.tools.run_preflight \\
        local/assessments/run_2026-09-10/case_06_mariposa_edu_gmbh.md \\
        --intake-dir mock/06_mariposa_edu_gmbh
"""
from __future__ import annotations

from typing import Any

from aaa.tools.run_preflight.archived import find_archived_run, reference_state
from aaa.tools.run_preflight.checks import Check, check_cgsa, check_model
from aaa.tools.run_preflight.declaration_checks import check_declaration, check_documents
from aaa.tools.run_preflight.header import BaselineError
from aaa.tools.run_preflight.reference import resolve_reference

__all__ = ["Check", "BaselineError", "preflight", "render"]


def preflight(doc_path: str, stage_a: dict[str, Any], stage_b: dict[str, Any],
              run_id: str | None = None) -> tuple[dict[str, Any], list[Check]]:
    """Compare a planned run against the baseline a case document pins.

    :param doc_path: The per-call assessment markdown for the case.
    :param stage_a: The Stage A payload the run would submit.
    :param stage_b: The Stage B payload the run would submit.
    :param run_id: Compare against this run instead of the archive's
        controlled comparison.
    :returns: ``(reference header, checks)``.
    :raises BaselineError: When the baseline run is not in the archive.
    """
    reference = resolve_reference(doc_path, run_id)
    state = reference_state(find_archived_run(reference["run_id"]))
    reference["state_kpis"] = {
        "regulatory_coverage_pct": state.get("regulatory_coverage_pct"),
        "final_verdict": state.get("final_verdict"),
        "completeness_score": state.get("completeness_score"),
    }
    return reference, [
        check_model(reference),
        check_cgsa(reference, state,
                   str(stage_a.get("provider_name") or ""),
                   str(stage_a.get("system_name") or "")),
        check_declaration(state, stage_a),
        check_documents(state, stage_b),
    ]


def render(reference: dict[str, Any], checks: list[Check]) -> str:
    """Format a preflight result for a terminal.

    :param reference: The parsed document header.
    :param checks: The checks that were run.
    :returns: The report text.
    """
    blocked = [c for c in checks if c.blocking and not c.ok]
    lines = [
        f"reference : {reference['doc']}",
        f"            baseline run {reference['run_id']} "
        f"(from {reference.get('baseline_source')}) · {reference.get('engagement_id')}",
        f"            assessed run {reference.get('assessed_run_id')} "
        "— the document's subject, pre-fix; not the baseline",
        f"            model {reference.get('model')} / {reference.get('provider_pin')}",
        f"            CGSA  {reference.get('cgsa_note')}",
        f"            expects {reference['state_kpis']}",
        "",
    ]
    for check in checks:
        mark = "ok  " if check.ok else ("BLOCK" if check.blocking else "warn")
        lines.append(f"  [{mark}] {check.name:12} {check.detail}")
    lines += ["", "NOT COMPARABLE — do not dispatch:" if blocked
              else "comparable with the reference run."]
    lines += [f"  - {c.name}" for c in blocked]
    return "\n".join(lines)
