"""The one finding a phase raises when it produced no report at all."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.phases.verification.no_report.failure import _cause
from aaa.tools.findings import make_finding


def _record_finding(state: dict, tids: list[str], articles: list[str],
                    failure: dict[str, Any], *,
                    phase_id: str, phase_label: str) -> None:
    """Raise this phase's one no-report finding, replacing any earlier attempt's."""
    from aaa.agents.tier1.phases.verification.unadmitted import clear_phase_finding

    finding_id = f"{phase_id or 'P?'}-VERIFY-NOREPORT"
    clear_phase_finding(state, finding_id)
    findings: list[dict[str, Any]] = state.setdefault("blocking_findings", [])
    findings.append(make_finding(
        finding_id=finding_id,
        description=(
            f"{phase_label} produced no report: {_cause(failure)}. No artefact was "
            f"written in its place — {', '.join(tids)} do not exist — so the "
            f"article(s) this phase was accountable for are recorded "
            f"INSUFFICIENT_EVIDENCE rather than assessed."),
        materiality="possibly_material",
        articles=articles,
        source_phase=phase_id or phase_label,
        recommendation=("Re-run this phase before the report is signed. If it fails "
                        "again, the articles above cannot be concluded on and the "
                        "opinion must say so."),
    ))


__all__ = ["_record_finding"]
