"""Turning one phase's carried Verifier issues into findings and evidence-gap records."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.phases.verification.provider_findings.cited import cited_articles
from aaa.agents.tier1.phases.verification.provider_findings.entries import (
    carried,
    finding,
    gap_record,
)
from aaa.agents.tier1.phases.verification.provider_findings.graded import (
    Load,
    capped,
    graded_statuses,
)
from aaa.agents.tier1.phases.verification.provider_findings.unmeasured import as_measured
from aaa.platform.state.admission import admitted_artefacts
from aaa.tools.regulatory_coverage.engagement_scope import keep_in_scope


def _collect(state: dict, tid_articles: dict[str, list[str]], phase_id: str,
             phase_label: str, load: Load | None) -> tuple[list[dict], list[dict]]:
    """``(findings, gap records)`` for this phase's admitted artefacts."""
    admitted, critiques = admitted_artefacts(state), state.get("verifier_critiques") or {}
    findings: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    for tid, articles in tid_articles.items():
        if tid not in admitted:
            continue
        scoped = keep_in_scope(state, articles, claimed_by=tid)
        issues = [as_measured(i, tid, state)
                  for i in (critiques.get(tid) or {}).get("issues") or [] if carried(i)]
        statuses = graded_statuses(tid, state, load)
        for n, raw in enumerate(issues, start=1):
            about = cited_articles(raw, scoped)
            issue = capped(raw, about, statuses)
            findings.append(finding(issue, f"{phase_id or 'P?'}-VER-{tid.split('_')[0]}-{n}",
                                    tid, about, phase_id))
            record = gap_record(issue, tid, about, phase_id=phase_id, phase_label=phase_label)
            gaps += [record] if record else []
    return findings, gaps


__all__ = ["_collect"]
